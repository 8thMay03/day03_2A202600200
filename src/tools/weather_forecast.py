import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from pathlib import Path


def crawl_thoitiet_hourly():
    url = "https://thoitiet.vn/ha-noi/theo-gio"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://thoitiet.vn/ha-noi",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        # print(f"✅ Kết nối thành công - Status: {response.status_code}")
    except Exception as e:
        # print(f"❌ Lỗi kết nối: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    data = {
        "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "location": "Hà Nội",
        "source": url,
        "hourly_forecast": [],
    }

    # Mỗi giờ nằm trong thẻ <details class="weather-day">
    rows = soup.select("details.weather-day")
    # print(f"📊 Tìm thấy {len(rows)} dòng thời tiết theo giờ")

    for row in rows:
        hour_data = {}

        # === PHẦN SUMMARY (luôn hiển thị) ===

        # 1. Thời gian - trong h2.summary-day > span
        time_el = row.select_one("h2.summary-day span")
        if time_el:
            hour_data["time"] = time_el.get_text(strip=True)

        # 2. Nhiệt độ - trong div.summary-temperature
        #    span.summary-temperature-min = nhiệt độ thực
        #    span.summary-temperature-max-value = nhiệt độ cảm nhận (feels like)
        temp_min = row.select_one("span.summary-temperature-min")
        if temp_min:
            hour_data["temperature"] = temp_min.get_text(strip=True)

        temp_max = row.select_one("span.summary-temperature-max-value")
        if temp_max:
            hour_data["feels_like"] = temp_max.get_text(strip=True)

        # 3. Tình trạng thời tiết - trong div.summary-description
        cond_span = row.select_one("span.summary-description-detail")
        if cond_span:
            hour_data["condition"] = cond_span.get_text(strip=True)
        else:
            # Fallback: lấy từ alt của img
            img = row.select_one("img.summary-img")
            if img and img.get("alt"):
                hour_data["condition"] = img["alt"]

        # Icon URL
        icon_img = row.select_one("img.summary-img")
        if icon_img and icon_img.get("src"):
            hour_data["icon_url"] = icon_img["src"]

        # 4. Độ ẩm - trong div.summary-humidity
        humidity_div = row.select_one("div.summary-humidity")
        if humidity_div:
            # Lấy span cuối cùng chứa giá trị %
            spans = humidity_div.find_all("span")
            for s in spans:
                text = s.get_text(strip=True)
                if "%" in text and not s.find("i"):  # Bỏ qua span chứa icon
                    hour_data["humidity"] = text
                    break

        # 5. Tốc độ gió - trong div.summary-speed
        wind_div = row.select_one("div.summary-speed")
        if wind_div:
            spans = wind_div.find_all("span")
            for s in spans:
                text = s.get_text(strip=True)
                if "km/giờ" in text:
                    hour_data["wind_speed"] = text
                    break

        # === PHẦN DETAIL (mở rộng) ===
        # Nằm trong div.weather-content > div.weather-detail
        detail_div = row.select_one("div.weather-content")
        if detail_div:
            detail_items = detail_div.select("div.weather-content-item")
            for item in detail_items:
                # Lấy label (h6) và value (span.op-8 hoặc h3.op-8)
                label_el = item.select_one("h6.fw-bold")
                value_el = item.select_one(".op-8.fw-bold")

                if label_el and value_el:
                    label_text = label_el.get_text(strip=True)
                    value_text = value_el.get_text(strip=True)

                    if "UV" in label_text:
                        hour_data["uv_index"] = value_text
                    elif "Tầm nhìn" in label_text:
                        hour_data["visibility"] = value_text
                    elif "Áp suất" in label_text:
                        hour_data["pressure"] = value_text

                # Mô tả chi tiết (weather-content-item-description)
                if "weather-content-item-description" in item.get("class", []):
                    desc_span = item.select_one("span")
                    if desc_span:
                        hour_data["description"] = desc_span.get_text(strip=True)

        # Chỉ thêm nếu có thời gian
        if hour_data.get("time"):
            data["hourly_forecast"].append(hour_data)

        # Chỉ lấy 12 giờ đầu tiên
        if len(data["hourly_forecast"]) >= 12:
            break

    # Lưu vào file JSON
    filename = f"thoitiet_ha_noi_hourly_{datetime.now().strftime('%Y%m%d_%H%M')}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # print(f"\n🎉 ĐÃ CRAWL THÀNH CÔNG {len(data['hourly_forecast'])} giờ thời tiết!")
    # print(f"📁 File được lưu: {filename}")

    # Hiển thị toàn bộ kết quả
    # if data["hourly_forecast"]:
    #     print("\n=== DỮ LIỆU 12 GIỜ ===")
    #     print(json.dumps(data["hourly_forecast"], ensure_ascii=False, indent=2))
    # else:
    #     print("⚠️ Không lấy được dữ liệu nào. Trang web có thể thay đổi cấu trúc.")

    return data


def _find_latest_cached_weather_file():
    """
    Find the newest cached weather JSON file in common locations.
    Priority by modified time across:
    - project root
    - src/tools
    """
    project_root = Path(__file__).resolve().parents[2]
    candidate_dirs = [project_root, project_root / "src" / "tools"]
    pattern = "thoitiet_ha_noi_hourly_*.json"

    files = []
    for directory in candidate_dirs:
        files.extend(directory.glob(pattern))

    if not files:
        return None

    return max(files, key=lambda f: f.stat().st_mtime)


def get_weather_forecast():
    """
    Use cached weather file if it exists, otherwise crawl fresh data.
    """
    cached_file = _find_latest_cached_weather_file()
    if cached_file and cached_file.exists():
        with open(cached_file, "r", encoding="utf-8") as f:
            return json.load(f)

    return crawl_thoitiet_hourly()


if __name__ == "__main__":
    crawl_thoitiet_hourly()