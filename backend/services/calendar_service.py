from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import json
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CONFIG_PATH = Path(__file__).parent.parent / "config"

def get_calendar_service():
    """Authenticate và return Calendar service"""
    creds = None
    token_path = CONFIG_PATH / "token.json"
    
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CONFIG_PATH / "credentials.json"), SCOPES)
            creds = flow.run_local_server(port=0)
        
        token_path.write_text(creds.to_json())
    
    return build('calendar', 'v3', credentials=creds)

async def list_events(max_results: int = 10):
    """Lấy danh sách events"""
    service = get_calendar_service()
    events_result = service.events().list(
        calendarId='primary',
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])