import os
from pathlib import Path

# App info
APP_NAME = "AssistAI"
APP_VERSION = "0.1.0"

# Backend configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
API_BASE_URL = f"{BACKEND_URL}/api"

# Paths
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"

# API Endpoints
class API:
    # Auth
    AUTH_STATUS = f"{API_BASE_URL}/auth/status"
    AUTH_LOGIN = f"{API_BASE_URL}/auth/login"
    AUTH_LOGOUT = f"{API_BASE_URL}/auth/logout"
    
    # Calendar
    CALENDAR_EVENTS = f"{API_BASE_URL}/calendar/events"
    CALENDAR_SMART_CREATE = f"{API_BASE_URL}/calendar/events/smart-create"
    CALENDAR_SMART_UPDATE = f"{API_BASE_URL}/calendar/events/smart-update"
    CALENDAR_SMART_DELETE = f"{API_BASE_URL}/calendar/events/smart-delete"
    
    # Chat
    CHAT = f"{API_BASE_URL}/chat"