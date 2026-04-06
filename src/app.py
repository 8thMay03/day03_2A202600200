import os
from src.agent.agent import ReActAgent
# from src.core.gemini_provider import GeminiProvider
from src.core.openai_provider import OpenAIProvider
from src.tools.weather_forecast import get_weather_forecast
from src.tools.suggest_outfit import suggest_outfit
from src.tools.get_event import get_nearby_places_serpapi

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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

agent = ReActAgent(
    llm=OpenAIProvider(
        model_name="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
    ),
    tools=tools,
)
# agent = ReActAgent(
#     llm=GeminiProvider(
#         model_name="gemini-2.5-flash",
#         api_key=os.getenv("GOOGLE_API_KEY"),
#     ),
#     tools=tools,
# )

while True:
    user_input = input("You: ")
    response = agent.run(user_input)
    print(response)