"""Google Calendar Service"""
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session
from services.auth_service import get_credentials_for_user
from config.config import settings
from typing import Optional, List, Dict
import datetime
from exceptions import (
    GoogleCalendarError,
    NoOAuthTokenError,
    EventConflictError,
    ValidationError,
    EventNotFoundError,
)


SCOPES = settings.google_scopes_list


def get_calendar_service(db: Session, user_id: int) -> object:
    """
    Authenticate and return Calendar service for user
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Google Calendar service object
        
    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleCalendarError: If service creation fails
    """
    try:
        creds = get_credentials_for_user(db, user_id)
        
        # Check and refresh if needed
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                raise GoogleCalendarError(f"Token refresh failed: {str(e)}")
        
        service = build('calendar', 'v3', credentials=creds)
        return service
        
    except NoOAuthTokenError:
        raise
    except GoogleCalendarError:
        raise
    except Exception as e:
        raise GoogleCalendarError(f"Failed to create calendar service: {str(e)}")


async def list_events(
    db: Session,
    user_id: int,
    max_results: int = 100,
    days_ahead: int = 7,
    days_back: int = 0,
) -> List[Dict]:
    """
    Get list of events from today to next N days
    
    Args:
        db: Database session
        user_id: User ID
        max_results: Maximum results to return
        days_ahead: Number of days to look ahead (default: 7)
        
    Returns:
        List of event dicts
        
    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleCalendarError: If calendar operation fails
    """
    try:
        service = get_calendar_service(db, user_id)
        
        # Get from days_back days before today
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        time_min = (today - datetime.timedelta(days=days_back)).isoformat() + 'Z'
        
        # To end of N days ahead
        end_date = today + datetime.timedelta(days=days_ahead)
        time_max = end_date.isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
        
    except (NoOAuthTokenError, GoogleCalendarError):
        raise
    except HttpError as e:
        raise GoogleCalendarError(f"Calendar API error: {str(e)}")
    except Exception as e:
        raise GoogleCalendarError(f"Failed to list events: {str(e)}")


async def create_event(
    db: Session,
    user_id: int,
    summary: str,
    start_datetime: str,
    end_datetime: str,
    description: Optional[str] = None,
    recurrence: Optional[List[str]] = None,
    attendees: Optional[List[str]] = None,
    location: Optional[str] = None,
    timezone: str = "Asia/Ho_Chi_Minh",
) -> Dict:
    """
    Create an event in user's calendar
    
    Args:
        db: Database session
        user_id: User ID
        summary: Event title (required)
        start_datetime: Start time ISO format (required)
        end_datetime: End time ISO format (required)
        description: Event description
        recurrence: RRULE format list
        attendees: List of attendee emails
        location: Event location
        
    Returns:
        Created event dict
        
    Raises:
        ValidationError: If required fields are missing or invalid
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleCalendarError: If event creation fails
    """
    # Validate required fields
    if not summary or not summary.strip():
        raise ValidationError("Event summary cannot be empty")
    if not start_datetime or not end_datetime:
        raise ValidationError("Start and end times are required")
    
    try:
        service = get_calendar_service(db, user_id)
        
        # Create event object
        event = {
            'summary': summary.strip(),
            'start': {
                'dateTime': start_datetime,
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': timezone,
            }
        }
        
        if description:
            event['description'] = description
        
        if recurrence:
            event['recurrence'] = recurrence
        
        if attendees:
            event['attendees'] = [{'email': email.strip()} for email in attendees if email.strip()]
        
        if location:
            event['location'] = location
        
        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all'
        ).execute()
        
        return created_event
        
    except (ValidationError, NoOAuthTokenError, GoogleCalendarError):
        raise
    except HttpError as e:
        raise GoogleCalendarError(f"Calendar API error: {str(e)}")
    except Exception as e:
        raise GoogleCalendarError(f"Failed to create event: {str(e)}")


async def update_event(
    db: Session,
    user_id: int,
    event_id: str,
    summary: Optional[str] = None,
    start_datetime: Optional[str] = None,
    end_datetime: Optional[str] = None,
    description: Optional[str] = None,
    recurrence: Optional[List[str]] = None,
    attendees: Optional[List[str]] = None,
    location: Optional[str] = None,
    timezone: str = "Asia/Ho_Chi_Minh",
) -> Dict:
    """
    Update an event in user's calendar
    
    Args:
        db: Database session
        user_id: User ID
        event_id: Event ID to update (required)
        summary: New event title
        start_datetime: New start time
        end_datetime: New end time
        description: New description
        recurrence: New recurrence rules
        attendees: New attendee list
        location: New location
        
    Returns:
        Updated event dict
        
    Raises:
        ValidationError: If event_id is missing
        EventNotFoundError: If event not found
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleCalendarError: If update fails
    """
    if not event_id:
        raise ValidationError("Event ID is required")
    
    try:
        service = get_calendar_service(db, user_id)
        
        # Get current event
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        # Update only provided fields
        if summary is not None:
            event['summary'] = summary.strip()
        
        if description is not None:
            event['description'] = description
        
        if start_datetime is not None and end_datetime is not None:
            event['start'] = {'dateTime': start_datetime, 'timeZone': timezone}
            event['end'] = {'dateTime': end_datetime, 'timeZone': timezone}
        
        if recurrence is not None:
            event['recurrence'] = recurrence
        
        if attendees is not None:
            event['attendees'] = [{'email': email.strip()} for email in attendees if email.strip()]
        
        if location is not None:
            event['location'] = location
        
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event,
            sendUpdates='all'
        ).execute()
        
        return updated_event
        
    except (ValidationError, NoOAuthTokenError, GoogleCalendarError):
        raise
    except HttpError as e:
        if e.resp.status == 404:
            raise EventNotFoundError(event_id=event_id)
        raise GoogleCalendarError(f"Calendar API error: {str(e)}")
    except Exception as e:
        raise GoogleCalendarError(f"Failed to update event: {str(e)}")


async def delete_event(
    db: Session,
    user_id: int,
    event_id: str
) -> bool:
    """
    Delete an event from user's calendar
    
    Args:
        db: Database session
        user_id: User ID
        event_id: Event ID to delete
        
    Returns:
        True if successful
        
    Raises:
        ValidationError: If event_id is missing
        EventNotFoundError: If event not found
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleCalendarError: If deletion fails
    """
    if not event_id:
        raise ValidationError("Event ID is required")
    
    try:
        service = get_calendar_service(db, user_id)
        
        service.events().delete(
            calendarId='primary',
            eventId=event_id,
            sendUpdates='all'
        ).execute()
        
        return True
        
    except (ValidationError, NoOAuthTokenError, GoogleCalendarError):
        raise
    except HttpError as e:
        if e.resp.status == 404:
            raise EventNotFoundError(event_id=event_id)
        raise GoogleCalendarError(f"Calendar API error: {str(e)}")
    except Exception as e:
        raise GoogleCalendarError(f"Failed to delete event: {str(e)}")