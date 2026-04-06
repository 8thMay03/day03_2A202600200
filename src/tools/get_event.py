import requests
import json
import os
import re

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")


def _extract_distance(place: dict) -> str:
    """
    Extract distance text from SerpAPI local result.
    """
    direct = place.get("distance")
    if direct:
        return str(direct)

    for ext in place.get("extensions", []) or []:
        text = str(ext)
        if "km" in text.lower() or "m" in text.lower():
            return text

    return "Không rõ khoảng cách"


def _distance_to_km(distance_text: str) -> float:
    """
    Convert distance text to km for sorting.
    Supports values like: '1.2 km', '850 m', '0,9 km'.
    Unknown values are pushed to the end.
    """
    if not distance_text:
        return float("inf")

    text = str(distance_text).strip().lower().replace(",", ".")
    match = re.search(r"(\d+(\.\d+)?)", text)
    if not match:
        return float("inf")

    value = float(match.group(1))
    if " km" in text or text.endswith("km"):
        return value
    if " m" in text or text.endswith("m"):
        return value / 1000.0
    return float("inf")



# GẦN ĐỊA ĐIỂM CAFE
# =====================
def get_nearby_places_serpapi(payload=None):
    """
    Find nearby cafe places with SerpAPI.
    Accepted payload:
    - None: default Hanoi coordinates + query 'cafe'
    - str: query only (e.g. 'cafe yên tĩnh')
    - dict: {"lat": 21.0285, "lon": 105.8542, "query": "cafe"}
    """
    lat = 21.0285
    lon = 105.8542
    query = "cafe"

    if isinstance(payload, str) and payload.strip():
        query = payload.strip()
    elif isinstance(payload, dict):
        lat = payload.get("lat", lat)
        lon = payload.get("lon", lon)
        query = payload.get("query", query)

    if not SERPAPI_KEY:
        return json.dumps(
            {"error": "SERPAPI_KEY is missing. Please set environment variable SERPAPI_KEY."},
            ensure_ascii=False,
            indent=2,
        )

    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_maps",
        "q": query,
        "ll": f"@{lat},{lon},15z",
        "type": "search",
        "api_key": SERPAPI_KEY
    }

    resp = requests.get(url, params=params, timeout=20)
    data = resp.json()

    places = []
    for r in data.get("local_results", []):
        distance_text = _extract_distance(r)
        places.append({
            "name": r.get("title"),
            "address": r.get("address"),
            "rating": r.get("rating"),
            "open": r.get("open_state") if r.get("open_state") is not None else "Open 24 hours",
            "type": r.get("type"),
            "distance": distance_text,
            "distance_km": round(_distance_to_km(distance_text), 3),
        })

    places.sort(key=lambda x: x.get("distance_km", float("inf")))

    # ✅ TRẢ VỀ JSON
    return json.dumps(places, ensure_ascii=False, indent=2)



# =====================
# LẤY SỰ KIỆN HÀ NỘI
# =====================
# def get_local_events_serpapi_today(location="Hanoi"):
#     url = "https://serpapi.com/search.json"

#     params = {
#         "engine": "google",
#         "q": f"events near {location}",
#         "api_key": SERPAPI_KEY
#     }

#     resp = requests.get(url, params=params)
#     data = resp.json()
#     events = []
#     for e in data.get("events_results", []):
#         events.append({
#             "title": e.get("title"),
#             "address": e.get("address"),
#             "link": e.get("link")
#         })

#     return events


# events = get_local_events_serpapi_today()

# # LƯU FILE events.json
# with open("events.json", "w", encoding="utf-8") as f:
#     json.dump(events, f, ensure_ascii=False, indent=2)


# print("✅ Saved places.json & events.json")
