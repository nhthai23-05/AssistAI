"""
AUTH.PY - Authentication và Authorization Handler
================================================
Mục đích: Xử lý tất cả authentication flows cho external services
Chức năng:
- Google OAuth2 flow implementation
- Token storage và refresh mechanism
- Credential validation và expiry handling
- Multi-account support
- Secure token storage (encryption)
- Permission scope management
- Authentication error handling
Dependencies: None (base utility)
"""
"""
AUTH.PY - Google OAuth2 Authentication Flow
==========================================
"""
import os
import json
import google
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class GoogleAuth:
    def __init__(self, credentials_file=None, token_file=None, scopes=None):
        # Import config ở đây để tránh circular import
        from utils.config import get_config
        
        config = get_config()
        google_config = config.google
        
        # Dùng config từ settings.json
        self.credentials_file = credentials_file or google_config.credentials_file
        self.token_file = token_file or google_config.token_file
        self.scopes = scopes or google_config.scopes
    
    def authenticate(self):
        """
        FLOW AUTHENTICATION:
        1. Kiểm tra token.json có tồn tại không
        2. Nếu có và còn valid -> dùng luôn
        3. Nếu không -> chạy OAuth flow với credentials.json
        4. Lưu token mới vào token.json
        """
        creds = None
        
        # Bước 1: Kiểm tra token đã lưu
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        
        # Bước 2: Nếu không có token hoặc token hết hạn
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh token nếu hết hạn
                creds.refresh(Request())
            else:
                # Chạy OAuth flow với credentials.json
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
            
            # Bước 3: Lưu token để lần sau không cần auth lại
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    
    def get_calendar_service(self):
        """Trả về Google Calendar service object"""
        creds = self.authenticate()
        return build('calendar', 'v3', credentials=creds)
    
    def get_sheets_service(self):
        """Trả về Google Sheets service object"""
        creds = self.authenticate()
        return build('sheets', 'v4', credentials=creds)