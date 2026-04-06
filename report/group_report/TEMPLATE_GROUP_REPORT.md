# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: C401_D3 

- **Team Members**: 
    - Lưu Quang Lực
    - Đinh Văn Thư
    - Nguyễn Quốc Khánh
    - Nguyễn Bá Khánh
    - Lý Quốc An
    - Lưu Thị Ngọc Quỳnh
- **Deployment Date**: 2026 - 04 - 06

---

## 1. Executive Summary


Kết quả thực nghiệm cho thấy ReAct Agent đạt hiệu quả cao hơn chatbot baseline, đặc biệt trong các câu hỏi yêu cầu:

Phân tích ngữ cảnh người dùng
Kết hợp nhiều nguồn thông tin
Chủ động gọi công cụ bên ngoài (ví dụ: dự báo thời tiết, tìm quán cà phê gần vị trí)
- Có thể sai ở việc khi khác yêu cầu tại nhóm đang gắn hẳn việc là đi cafe chưa có thêm dữ liệu với case như việc đi bơi đi công viên ...
---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
*Diagram or description of the Thought-Action-Observation loop.*
Quy trình hoạt động của ReAct Agent được mô tả như sau:


Thought (Suy luận):
Agent phân tích đầu vào của người dùng để xác định mục tiêu và thông tin còn thiếu.
Ví dụ: với câu hỏi “Tôi muốn đi uống cafe”, agent suy luận rằng cần thông tin về địa điểm và ngữ cảnh như vị trí hoặc thời tiết.


Action (Hành động):
Nếu thông tin cần thiết không có sẵn, agent sẽ lựa chọn một công cụ phù hợp (ví dụ: tra cứu thời tiết hoặc tìm địa điểm quán cafe gần đó) và thực hiện lời gọi công cụ.


Observation (Quan sát):
Agent nhận kết quả từ công cụ, cập nhật lại ngữ cảnh nội bộ và tiếp tục suy luận hoặc tạo câu trả lời cuối cùng cho người dùng.
.



## 2.2 Tool Definitions (Inventory)

Bảng dưới đây mô tả các công cụ (tools) được tích hợp trong hệ thống ReAct Agent. Các công cụ này cho phép agent truy cập dữ liệu thời gian thực và thực hiện các tác vụ cụ thể nhằm nâng cao khả năng giải quyết các truy vấn nhiều bước.

| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `weather_forecast` | `string` (location) | Lấy thông tin dự báo thời tiết theo giờ tại Hà Nội để hỗ trợ tư vấn hoạt động ngoài trời |
| `suggest_outfit` | `json` (weather data) | Gợi ý trang phục phù hợp dựa trên dữ liệu thời tiết như nhiệt độ, độ ẩm và điều kiện thời tiết |
| `get_nearby_places_serpapi` | `string` (query / location) | Gợi ý các quán cà phê hoặc địa điểm giải trí gần vị trí người dùng (mặc định Hà Nội) |

### Ghi chú
- Ba công cụ đầu tiên (`weather_forecast`, `suggest_outfit`, `get_nearby_places_serpapi`) là **các tool cốt lõi** được sử dụng trực tiếp trong quá trình ReAct của agent.

### 2.3 LLM Providers Used

Team sử dụng GPT-4o-mini để search chính 
và Gemini 1.5 flash để sử dụng nếu hết tokens 


## 3. Telemetry & Performance Dashboard

*Analyze the industry metrics collected during the final test run.*

Độ trễ trung bình ví dụ: 3000ms 
Độ trễ tối đa : 6000ms 
Số token trung bình cho mỗi tác vụ: 1000 tokens
Tổng chi phí của toàn bộ bộ kiểm thử: 0.1 USD


## 4. Root Cause Analysis (RCA) - Failure Traces

*Deep dive into why the agent failed.*




 **Input**:" Tôi muốn đi bơi "
 **Observation**:Agent gọi  "get_nearby_places_serpapi" sẽ hiện ra các quán cafe không hiện bể bơi
 **Root Cause**Root Cause (Nguyên nhân gốc rễ): nguyên nhân là nhóm đang thiếu dữ liệu địa điểm khác chưa thể viết thêm dữ liệu về quán cafe 


## 5. Ablation Studies & Experiments

Diff:
Prompt v2 được cải tiến bằng cách:

Nhấn mạnh việc sử dụng thông tin thời tiết trước khi đưa ra gợi ý hoạt động
Hướng dẫn agent kết hợp suy luận ngữ cảnh (nhiệt độ, thời tiết) với hành động (gợi ý địa điểm) trước khi trả lời
Giảm các câu trả lời chung chung, yêu cầu agent đưa ra gợi ý cụ thể và có căn cứ



Result:
So sánh hai log thực nghiệm cho thấy:

Prompt v2 giúp agent giảm lỗi trả lời thiếu liên quan đến ngữ cảnh người dùng
Agent thực hiện nhiều bước suy luận hơn (3 steps thay vì 2) đối với các yêu cầu hoạt động ngoài trời
Chất lượng câu trả lời được cải thiện rõ rệt, đặc biệt trong việc kết hợp thời tiết + đề xuất hoạt động

You: tôi muốn đi bơi
{"timestamp": "2026-04-06T09:48:52.383657", "event": "AGENT_START", "data": {"input": "tôi muốn đi bơi", "model": "gpt-4o-mini"}}
{"timestamp": "2026-04-06T09:49:00.758537", "event": "AGENT_END", "data": {"steps": 3, "reason": "final_answer"}}
Thời tiết hiện tại ở Hà Nội rất nóng với nhiệt độ khoảng 33-34 độ C, tạo điều kiện lý tưởng cho việc đi bơi.

### Experiment 2 (Bonus): Chatbot vs Agent


| Trường hợp | Kết quả Chatbot | Kết quả Agent | Hệ thống tốt hơn |
| :--- | :--- | :--- | :--- |
| Câu hỏi đơn giản | Đúng | Đúng | Hòa |
| Truy vấn nhiều bước | Trả lời chung chung / thiếu ngữ cảnh | Phân tích thời tiết + gợi ý cụ thể | **Agent** |




## 6. Production Readiness Review

Phần này đánh giá mức độ sẵn sàng triển khai hệ thống AI Agent vào môi trường thực tế, bao gồm các khía cạnh về bảo mật, kiểm soát rủi ro và khả năng mở rộng.

### Security
- Thực hiện **kiểm tra và làm sạch đầu vào (input sanitization)** cho tất cả tham số trước khi gọi tool nhằm tránh lỗi định dạng hoặc lạm dụng API.
- Không cho phép agent truyền trực tiếp dữ liệu do người dùng nhập vào các công cụ bên ngoài mà không qua bước xác thực.
- Quản lý và bảo mật **API keys** thông qua biến môi trường (`.env`) thay vì hard-code trong mã nguồn.


### Guardrails
- Áp dụng **giới hạn số vòng lặp ReAct tối đa (ví dụ: 3 loops)** để tránh tình trạng agent lặp vô hạn, gây tăng chi phí và độ trễ.
- Theo dõi và log lại tất cả các bước **Thought – Action – Observation** để phục vụ debug và phân tích lỗi.
- Thiết lập cơ chế fallback: nếu agent gọi tool thất bại nhiều lần, hệ thống sẽ trả về câu trả lời an toàn thay vì tiếp tục thử.

### Scaling
- Thiết kế hệ thống theo hướng **module hóa**, cho phép dễ dàng thay thế hoặc bổ sung tool mới.
- Với các luồng hội thoại và quyết định phức tạp hơn, có thể **chuyển sang LangGraph** để hỗ trợ branching logic, parallel actions và quản lý trạng thái tốt hơn.
- Hỗ trợ nhiều LLM providers (OpenAI, Gemini) giúp hệ thống linh hoạt và sẵn sàng mở rộng trong môi trường production.


---

> [!NOTE]
> Submit this report by renaming it to `GROUP_REPORT_[TEAM_NAME].md` and placing it in this folder.
