THEME = {
    "coffee_dark": "#2C1810",
    "coffee_medium": "#6B3A2A",
    "coffee_light": "#C4956A",
    "cream": "#F5ECD7",
    "cream_dark": "#E8D5B0",
    "sidebar_bg": "#3D2314",
    "sidebar_text": "#F0E0C8",
    "sidebar_muted": "#A07860",
    "chat_bg": "#FAF6F0",
    "msg_bot_bg": "#FFFFFF",
    "msg_user_bg": "#6B3A2A",
    "border": "rgba(107,58,42,0.15)",
    "tag_bg": "#F0D9C0",
    "tag_text": "#6B3A2A",
}

STREAMLIT_CONFIG = """
<style>
    [data-testid="stSidebar"] {
        background-color: #3D2314;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: #F0E0C8 !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #F0E0C8 !important;
    }
    .stChatMessage p {
        color: #2C1810 !important;
    }
    .stChatInput textarea {
        background-color: #F5ECD7;
        border: 1px solid #E8D5B0;
        border-radius: 10px;
        color: #2C1810 !important;
    }
    .stButton > button {
        background-color: #6B3A2A;
        color: #F5ECD7 !important;
        border: none;
        border-radius: 8px;
    }
    .stButton > button:hover {
        background-color: #2C1810;
        color: #F5ECD7 !important;
    }
</style>
"""

APP_NAME = "☕ Barista IA"
APP_SUBTITLE = "Asistente de entrenamiento"
