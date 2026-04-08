from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from services.auth_service import get_credentials_for_user, has_valid_token
from config.config import settings
from typing import Optional
import datetime


SCOPES = settings.google_scopes_list


def get_calendar_service(db: Session, user_id: int) -> Optional:
    """
    Authenticate and return Calendar service for user
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Google Calendar service object, or None if authentication fails
    """
    try:
        # Get credentials from DB
        creds = get_credentials_for_user(db, user_id)
        
        if not creds:
            print(f"❌ No credentials found for user {user_id}")
            return None
        
        # Check and refresh if needed
        if creds.expired and creds.refresh_token:
            try:
                print("⏳ Refreshing expired token...")
                creds.refresh(Request())
                # Note: oauth_token_service will auto-update in DB via has_valid_token
                print("✅ Token refreshed")
            except Exception as e:
                print(f"❌ Token refresh failed: {e}")
                return None
        
        # Build and return Calendar service
        service = build('calendar', 'v3', credentials=creds)
        print(f"✅ Calendar service created for user {user_id}")
        return service
        
    except Exception as e:
        print(f"❌ Failed to create calendar service: {e}")
        return None


async def list_events(db: Session, user_id: int, max_results: int = 100):
    """
    Get list of events from today to next 7 days
    
    Args:
        db: Database session
        user_id: User ID  
        max_results: Maximum results to return
        
    Returns:
        List of events
    """
    try:
        service = get_calendar_service(db, user_id)
        
        if not service:
            return {"error": f"Failed to authenticate for user {user_id}"}
        
        # Get from 00:00 today
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
        print(f"❌ Failed to list events: {e}")
        raise


async def insert_events(
    db: Session,
    user_id: int,
    summary: str,
    description: str = None,
    start_datetime: str = None,  # Format: '2026-01-18T10:00:00+07:00'
    end_datetime: str = None,    # Format: '2026-01-18T11:00:00+07:00'
    recurrence: list = None,     # RRULE format, ví dụ: ['RRULE:FREQ=DAILY;COUNT=5']
    attendees: list = None,
    location: str = None
):
    """
    Create an event in user's calendar
    
    Args:
        db: Database session
        user_id: User ID
        summary: Event title
        description: Event description
        start_datetime: Start time
        end_datetime: End time
        recurrence: Recurrence rules
        attendees: List of attendee emails
        location: Event location
    """
    try:
        service = get_calendar_service(db, user_id)
        
        if not service:
            return {"error": f"Failed to authenticate for user {user_id}"}
        
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
        
        print(f"✅ Event created: {created_event.get('htmlLink')}")
        return created_event
        
    except Exception as e:
        print(f"❌ Failed to create event: {e}")
        raise


async def update_events(
    db: Session,
    user_id: int,
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
        service = get_calendar_service(db, user_id)
        
        if not service:
            return {"error": f"Failed to authenticate for user {user_id}"}
        
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

async def delete_events(db: Session, user_id: int, event_id: str):
    """
    Delete event from user's calendar
    
    Args:
        db: Database session
        user_id: User ID
        event_id: Event ID to delete
    """
    try:
        service = get_calendar_service(db, user_id)
        
        if not service:
            return {"error": f"Failed to authenticate for user {user_id}"}
        
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