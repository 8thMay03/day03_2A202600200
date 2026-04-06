import os
from typing import Any, Dict, Union
from src.core.gemini_provider import GeminiProvider

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def suggest_outfit(payload: Union[Dict[str, Any], str]) -> str:
    """
    Suggest outfit based on weather payload.
    Accepted payload:
    - dict: {"weather_data": {...}, "user_intent": "..."}
    - dict: weather fields directly
    - str: plain user intent
    """
    user_intent = "Gợi ý outfit cho việc đi cafe."
    weather_data: Any = payload

    if isinstance(payload, dict):
        weather_data = payload.get("weather_data", payload)
        user_intent = payload.get("user_intent", user_intent)
    elif isinstance(payload, str):
        user_intent = payload
        weather_data = {}

    result = GeminiProvider(
        model_name="gemini-2.5-flash",
        api_key=os.getenv("GOOGLE_API_KEY"),
    ).generate(
        prompt=(
            "You are a fashion assistant.\n"
            f"Weather data: {weather_data}\n"
            f"User intent: {user_intent}\n"
            "Return concise outfit suggestions in Vietnamese, suitable for going to a cafe."
        ),
    )
    return (result.get("content") or "").strip()