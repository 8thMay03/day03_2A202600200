import os
import sys
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Ensure project root is on sys.path so `src.*` imports work
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.agent import ReActAgent
from src.core.gemini_provider import GeminiProvider
from src.core.openai_provider import OpenAIProvider
from src.tools.weather_forecast import get_weather_forecast
from src.tools.suggest_outfit import suggest_outfit
from src.tools.get_event import get_nearby_places_serpapi

load_dotenv()

st.set_page_config(page_title="Cafe Outfit Assistant", page_icon="☕", layout="wide")
st.title("☕ Cafe Outfit Assistant")
st.caption("ReAct demo: weather -> outfit -> nearby cafes")


def build_tools():
    return [
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


def build_agent(provider_name: str) -> ReActAgent:
    tools = build_tools()
    if provider_name == "Gemini":
        llm = GeminiProvider(
            model_name="gemini-2.5-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
        )
    else:
        llm = OpenAIProvider(
            model_name="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    return ReActAgent(llm=llm, tools=tools)


if "messages" not in st.session_state:
    st.session_state.messages = []
if "provider" not in st.session_state:
    st.session_state.provider = "OpenAI"
if "agent" not in st.session_state:
    st.session_state.agent = build_agent(st.session_state.provider)


with st.sidebar:
    st.subheader("Cau hinh")
    provider = st.selectbox(
        "LLM Provider",
        options=["OpenAI", "Gemini"],
        index=0 if st.session_state.provider == "OpenAI" else 1,
    )

    key_ok = True
    if provider == "OpenAI" and not os.getenv("OPENAI_API_KEY"):
        key_ok = False
        st.warning("Thieu OPENAI_API_KEY trong .env")
    if provider == "Gemini" and not os.getenv("GOOGLE_API_KEY"):
        key_ok = False
        st.warning("Thieu GOOGLE_API_KEY trong .env")

    if provider != st.session_state.provider:
        st.session_state.provider = provider
        if key_ok:
            st.session_state.agent = build_agent(provider)
            st.success(f"Da chuyen sang {provider}")
        else:
            st.error("Khong the tao agent vi thieu API key")

    if st.button("Xoa lich su chat"):
        st.session_state.messages = []
        st.rerun()
    if st.button("Reset agent"):
        if key_ok:
            st.session_state.agent = build_agent(provider)
            st.success("Da reset agent")
        else:
            st.error("Khong the reset agent vi thieu API key")

    st.divider()
    st.caption("Run: streamlit run src/streamlit_app.py")


left, right = st.columns([2, 1])

with left:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Nhap cau hoi, vd: Hom nay di cafe mac gi va goi y quan gan toi")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Agent dang xu ly..."):
                try:
                    response = st.session_state.agent.run(prompt)
                except Exception as exc:
                    response = f"Loi khi chay agent: {exc}"
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

with right:
    st.subheader("Trace")
    history = getattr(st.session_state.agent, "history", [])
    if not history:
        st.info("Chua co buoc xu ly nao.")
    else:
        for item in history[-6:]:
            step = item.get("step", "?")
            action = item.get("action")
            if action:
                st.markdown(f"**Step {step}** - `{action}`")
            else:
                llm_text = (item.get("llm_output") or "").strip()
                short = llm_text[:120] + ("..." if len(llm_text) > 120 else "")
                st.markdown(f"**Step {step}** - {short}")
