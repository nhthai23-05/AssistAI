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
Dependencies: utils.config
"""
"""
AUTH.PY - Google OAuth2 Authentication Flow
==========================================
"""
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class GoogleAuth:
    def __init__(self, credentials_file="config/credentials.json"):
        self.credentials_file = credentials_file
        self.token_file = "config/token.json"  # File lưu token sau khi auth
        self.scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
    
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

if __name__ == "__main__":
    print("🔐 Testing Google Authentication...")
    
    try:
        # Tạo instance của GoogleAuth
        auth = GoogleAuth()
        
        # Test authenticate method
        print("📝 Starting authentication process...")
        creds = auth.authenticate()
        
        if creds and creds.valid:
            print("✅ Authentication successful!")
            print(f"📧 Authenticated user: {creds.service_account_email if hasattr(creds, 'service_account_email') else 'User account'}")
            
            # Test services
            print("\n🗓️ Testing Calendar service...")
            calendar_service = auth.get_calendar_service()
            print("✅ Calendar service created successfully!")
            
            print("\n📊 Testing Sheets service...")
            sheets_service = auth.get_sheets_service()
            print("✅ Sheets service created successfully!")
            
            # Optional: Test actual API call
            print("\n📋 Testing Calendar API call...")
            try:
                calendar_list = calendar_service.calendarList().list().execute()
                print(f"✅ Found {len(calendar_list.get('items', []))} calendars")
                for calendar in calendar_list.get('items', [])[:3]:  # Show first 3
                    print(f"   📅 {calendar.get('summary', 'Unknown')}")
            except Exception as api_error:
                print(f"⚠️ API call failed: {api_error}")
        else:
            print("❌ Authentication failed!")
            
    except FileNotFoundError:
        print("❌ Error: credentials.json not found!")
        print("💡 Make sure you have downloaded OAuth credentials from Google Cloud Console")
        print("💡 Place the file at: config/credentials.json")
        
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        print("💡 Check your credentials file and internet connection")