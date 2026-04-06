# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn_Bá_Khánh
- **Student ID**: 2A202600135
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*


 `src/tools/weather_forecast.py`  
  Triển khai công cụ lấy thông tin thời tiết hiện tại (nhiệt độ, điều kiện trời) để hỗ trợ các quyết định liên quan đến hoạt động ngoài trời.
- `src/tools/get_nearby_places_serpapi.py`  
  Xây dựng công cụ tìm kiếm các quán cà phê/địa điểm gần vị trí người dùng dựa trên SerpAPI.
- `src/tools/suggest_outfit.py`  
  Phát triển logic gợi ý trang phục dựa trên dữ liệu thời tiết thu được từ công cụ `weather_forecast`.
- `src/agent/agent.py` (cải tiến)  
  Tích hợp các tool vào vòng lặp ReAct (Thought – Action – Observation) và bổ sung log cho từng bước suy luận.

tools = [
    {
        "name": "weather_forecast",
        "description": "Lấy dự báo thời tiết theo giờ ở Hà Nội",
        "func": get_weather_forecast,
    },
    {
        "name": "suggest_outfit",
        "description": "Gợi ý trang phục dựa trên dữ liệu thời tiết",
        "func": suggest_outfit,
    },
    {
        "name": "get_nearby_places_serpapi",
        "description": "Gợi ý quán cafe gần vị trí người dùng (mặc định Hà Nội)",
        "func": get_nearby_places_serpapi,
    },
]

 
---



Trong một số trường hợp, agent đã **đưa ra gợi ý không phù hợp với mục tiêu của người dùng**.  
Cụ thể, với truy vấn *“tôi muốn đi bơi”*, agent vẫn tiếp tục gợi ý **các quán cà phê gần vị trí người dùng**, thay vì gợi ý địa điểm bơi lội hoặc hoạt động phù hợp với mục tiêu ban đầu.



## II. Debugging Case Study (10 Points)

Phần này phân tích một lỗi cụ thể đã xảy ra trong quá trình phát triển và chạy thử ReAct Agent, dựa trên dữ liệu thu thập từ hệ thống logging.

Trong một số trường hợp, agent đã **đưa ra gợi ý không phù hợp với mục tiêu của người dùng**.  
Cụ thể, với truy vấn *“tôi muốn đi bơi”*, agent vẫn tiếp tục gợi ý **các quán cà phê gần vị trí người dùng**, thay vì gợi ý địa điểm bơi lội hoặc hoạt động phù hợp với mục tiêu ban đầu.

### Log Source

Trích đoạn log ghi nhận sự kiện lỗi:

```text
You: tôi muốn đi bơi
{"timestamp": "2026-04-06T09:48:52.383657", "event": "AGENT_START", "data": {"input": "tôi muốn đi bơi", "model": "gpt-4o-mini"}}
{"timestamp": "2026-04-06T09:49:00.758537", "event": "AGENT_END", "data": {"steps": 3, "reason": "final_answer"}}
Thời tiết hiện tại ở Hà Nội rất nóng với nhiệt độ khoảng 33-34 độ C, tạo điều kiện lý tưởng cho việc đi bơi.
Các quán cafe ở gần: 1. Cafe A - 500m 2. Cafe B - 1km 3. Cafe C - 1.5km

```

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1. Reasoning: Vai trò của khối Thought so với Chatbot trực tiếp
Khối Thought cho phép agent thực hiện suy luận trung gian một cách tường minh trước khi đưa ra hành động hoặc câu trả lời cuối cùng. Nhờ đó, agent có thể:

Phân tích ý định của người dùng
Xác định thông tin còn thiếu
Quyết định có cần gọi công cụ hay không

2. Reliability: Khi nào Agent hoạt động kém hơn Chatbot?
Mặc dù mạnh hơn trong các truy vấn nhiều bước, agent có thể hoạt động kém hơn chatbot trong một số trường hợp:

Câu hỏi rất đơn giản, không cần suy luận hay công cụ (ví dụ: định nghĩa, câu hỏi kiến thức phổ thông)
Khi tool routing sai, agent gọi công cụ không phù hợp với mục tiêu người dùng
Khi prompt hoặc tool specification chưa đủ rõ ràng, dẫn đến over-reasoning hoặc hành động dư thừa

3. Observation: Vai trò của phản hồi từ môi trường (environment feedback)
Khối Observation đóng vai trò cầu nối giữa hành động và suy luận tiếp theo của agent. Kết quả trả về từ môi trường hoặc công cụ:

Cập nhật lại trạng thái ngữ cảnh
Ảnh hưởng trực tiếp đến bước Thought tiếp theo
Giúp agent điều chỉnh chiến lược (tiếp tục gọi tool khác hoặc kết thúc)

Ví dụ, khi agent nhận được thông tin thời tiết nhiệt độ 33–34°C, observation này khiến agent suy luận rằng các hoạt động ngoài trời như đi bơi là phù hợp. Không có observation, agent chỉ có thể dựa vào kiến thức huấn luyện sẵn, dễ dẫn đến câu trả lời chung chung hoặc sai lệch ngữ cảnh.
---



## IV. Future Improvements (5 Points)

Phần này trình bày các hướng cải tiến dựa trên những vấn đề và hành vi thực tế quan sát được trong quá trình chạy hệ thống ReAct Agent cho các truy vấn như “đi uống cafe” và “đi bơi”.

### Scalability
- Tách riêng **nhóm tool theo loại hoạt động** (ví dụ: ăn uống, thể thao, giải trí) để khi người dùng hỏi *“tôi muốn đi bơi”*, agent chỉ xét các tool liên quan đến hoạt động bơi lội, tránh gọi nhầm tool gợi ý quán cafe.

- Khi số lượng tool tăng lên, có thể chuyển sang **LangGraph** để quản lý luồng quyết định phức tạp theo từng intent (ví dụ: cafe → weather → outfit → place).

### Safety
- Thêm bước **xác định intent rõ ràng** trước khi ReAct loop bắt đầu, nhằm tránh trường hợp agent hiểu sai mục tiêu người dùng (ví dụ: đi bơi nhưng vẫn gợi ý quán cafe).

- Thiết lập cơ chế **fallback an toàn**, trong đó nếu agent không tìm được tool phù hợp, hệ thống sẽ trả lời ở mức gợi ý chung thay vì gọi sai công cụ.

### Performance
- Cache kết quả **thời tiết theo khu vực Hà Nội** trong một khoảng thời gian ngắn (ví dụ 10–15 phút) để giảm số lần gọi API không cần thiết.
- Rút gọn prompt cho các case đơn giản (ví dụ: “các quán cafe ở gần tôi”) để giảm số token và độ trễ.


---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
