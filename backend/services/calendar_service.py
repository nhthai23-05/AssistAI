from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import json
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/calendar']
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

async def list_events(max_results: int = 100):
    """Lấy danh sách events từ hôm nay đến 7 ngày tới"""
    try:
        import datetime
        service = get_calendar_service()
        
        # Lấy từ 00:00 hôm nay
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        time_min = today.isoformat() + 'Z'
        
        # Đến 23:59 ngày thứ 7
        week_end = today + datetime.timedelta(days=7)
        time_max = week_end.isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])
    except Exception as e:
        print(f"Lỗi khi lấy danh sách events: {e}")
        raise

async def insert_events(
    summary: str,
    description: str = None,
    start_datetime: str = None,  # Format: '2026-01-18T10:00:00+07:00'
    end_datetime: str = None,    # Format: '2026-01-18T11:00:00+07:00'
    recurrence: list = None,     # RRULE format, ví dụ: ['RRULE:FREQ=DAILY;COUNT=5']
    attendees: list = None,
    location: str = None
):
    try:
        service = get_calendar_service()
        
        # Tạo event object
        event = {
            'summary': summary,
        }
        
        # Thêm các trường optional
        if description:
            event['description'] = description
        
        if start_datetime and end_datetime:
            event['start'] = {
                'dateTime': start_datetime,
                'timeZone': 'Asia/Ho_Chi_Minh',
            }
            event['end'] = {
                'dateTime': end_datetime,
                'timeZone': 'Asia/Ho_Chi_Minh',
            }
        
        if recurrence:
            event['recurrence'] = recurrence
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        if location:
            event['location'] = location
        
        # Tạo event
        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all'
        ).execute()
        
        print(f"✓ Đã tạo event: {created_event.get('htmlLink')}")
        return created_event
        
    except Exception as e:
        print(f"✗ Lỗi khi tạo event: {e}")
        raise

async def update_events(
    event_id: str,
    summary: str = None,
    start_datetime: str = None,
    end_datetime: str = None,
    description: str = None,
    recurrence: list = None,
    attendees: list = None,
    location: str = None
):
    """
    Cập nhật event trong Google Calendar
    
    Args:
        event_id: ID của event cần update (BẮT BUỘC)
        summary: Tên event mới
        start_datetime: Thời gian bắt đầu mới
        end_datetime: Thời gian kết thúc mới
        description: Mô tả mới
        recurrence: Quy tắc lặp lại mới
        attendees: Danh sách email người tham gia mới
        location: Địa điểm mới
    """
    try:
        service = get_calendar_service()
        
        # Lấy event hiện tại
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        # Cập nhật các trường được cung cấp
        if summary:
            event['summary'] = summary
        
        if description is not None: 
            event['description'] = description
        
        if start_datetime and end_datetime:
            event['start'] = {
                'dateTime': start_datetime,
                'timeZone': 'Asia/Ho_Chi_Minh',
            }
            event['end'] = {
                'dateTime': end_datetime,
                'timeZone': 'Asia/Ho_Chi_Minh',
            }
        
        if recurrence is not None:
            event['recurrence'] = recurrence
        
        if attendees is not None:
            event['attendees'] = [{'email': email} for email in attendees]
        
        if location is not None:
            event['location'] = location
        
        # Cập nhật event
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event,
            sendUpdates='all'  # Gửi thông báo cho attendees
        ).execute()
        
        print(f"✓ Đã cập nhật event: {updated_event.get('htmlLink')}")
        return updated_event
        
    except Exception as e:
        print(f"✗ Lỗi khi cập nhật event: {e}")
        raise

async def delete_events(event_id: str):
    try:
        service = get_calendar_service()
        
        service.events().delete(
            calendarId='primary',
            eventId=event_id,
            sendUpdates='all'
        ).execute()
        
        print(f"✓ Đã xóa event ID: {event_id}")
        return {"message": "Event deleted successfully", "event_id": event_id}
        
    except Exception as e:
        print(f"✗ Lỗi khi xóa event: {e}")
        raise