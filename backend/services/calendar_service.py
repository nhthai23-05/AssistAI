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
    credentials_path = CONFIG_PATH / "credentials.json"
    
    # Kiểm tra file credentials.json có tồn tại không
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file credentials.json tại {credentials_path}\n"
            "Vui lòng tải về từ Google Cloud Console và đặt vào thư mục config/"
        )
    
    # Đọc token đã lưu nếu có
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception as e:
            print(f"Lỗi khi đọc token: {e}")
            print("Sẽ tiến hành đăng nhập lại...")
            creds = None
    
    # Refresh hoặc tạo mới credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Đang refresh token...")
                creds.refresh(Request())
            except Exception as e:
                print(f"Lỗi khi refresh token: {e}")
                print("Yêu cầu đăng nhập lại...")
                creds = None
        
        if not creds:
            print("\n" + "="*60)
            print("ĐĂNG NHẬP LẦN ĐẦU - CẦN CẤP QUYỀN")
            print("="*60)
            print("Trình duyệt sẽ mở để bạn đăng nhập Google và cấp quyền.")
            print("Sau khi cấp quyền, thông tin sẽ được lưu vào token.json")
            print("="*60 + "\n")
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), SCOPES)
                creds = flow.run_local_server(
                    port=8080,  # Port cố định, dễ config trong Google Console
                    prompt='consent',  # Luôn hiển thị màn hình đồng ý
                    success_message='Đăng nhập thành công! Bạn có thể đóng cửa sổ này.'
                )
                print("\n✓ Đăng nhập thành công!")
            except Exception as e:
                print(f"\n✗ Lỗi khi đăng nhập: {e}")
                raise
        
        # Lưu credentials
        try:
            token_path.write_text(creds.to_json())
            print(f"✓ Đã lưu token vào {token_path}")
        except Exception as e:
            print(f"✗ Lỗi khi lưu token: {e}")
    
    return build('calendar', 'v3', credentials=creds)

async def list_events(max_results: int = 10):
    """Lấy danh sách events"""
    try:
        service = get_calendar_service()
        events_result = service.events().list(
            calendarId='primary',
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])
    except Exception as e:
        print(f"Lỗi khi lấy danh sách events: {e}")
        raise