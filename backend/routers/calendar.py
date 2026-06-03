"""Calendar Router - Handles calendar endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from config.database import get_db
from services.calendar_service import list_events, create_event, update_event, delete_event
from services.auth_service import has_valid_token
from schemas.event import EventCreate, EventResponse, EventListResponse
from exceptions import NoValidTokenError

router = APIRouter(tags=["calendar"])


def _transform_event(item: dict) -> dict:
    start = item.get("start", {})
    end = item.get("end", {})
    return {
        "event_id": item.get("id"),
        "summary": item.get("summary", "(Không có tiêu đề)"),
        "start_datetime": start.get("dateTime") or start.get("date"),
        "end_datetime": end.get("dateTime") or end.get("date"),
        "description": item.get("description", ""),
        "location": item.get("location", ""),
        "attendees": [a.get("email", "") for a in item.get("attendees", [])],
    }


@router.get("/events")
async def get_events(
    user_id: int = Query(..., description="User ID", gt=0),
    max_results: int = Query(100, description="Max events", ge=1, le=500),
    days_ahead: int = Query(7, description="Days to look ahead", ge=1, le=90),
    days_back: int = Query(0, description="Days to look back", ge=0, le=90),
    db: Session = Depends(get_db)
):
    """
    Get calendar events for next N days
    
    - **user_id**: User ID (required)
    - **max_results**: Maximum events to return (default: 100)
    - **days_ahead**: Number of days to look ahead (default: 7)
    """
    # Validate authentication
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)
    
    raw = await list_events(db, user_id, max_results, days_ahead, days_back)
    events = [_transform_event(e) for e in raw]
    return {"events": events, "total": len(events)}


@router.post("/events")
async def create_event_handler(
    request: EventCreate,
    user_id: int = Query(..., description="User ID", gt=0),
    db: Session = Depends(get_db)
):
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    event = await create_event(
        db=db,
        user_id=user_id,
        summary=request.summary,
        start_datetime=request.start_datetime.isoformat(),
        end_datetime=request.end_datetime.isoformat(),
        description=request.description,
        location=request.location,
        attendees=request.attendees,
        recurrence=request.recurrence,
        timezone=request.timezone or "Asia/Ho_Chi_Minh",
    )

    return _transform_event(event)


@router.put("/events/{event_id}")
async def update_event_handler(
    event_id: str,
    request: EventCreate,
    user_id: int = Query(..., description="User ID", gt=0),
    db: Session = Depends(get_db)
):
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    event = await update_event(
        db=db,
        user_id=user_id,
        event_id=event_id,
        summary=request.summary,
        start_datetime=request.start_datetime.isoformat(),
        end_datetime=request.end_datetime.isoformat(),
        description=request.description,
        location=request.location,
        attendees=request.attendees,
        recurrence=request.recurrence,
        timezone=request.timezone or "Asia/Ho_Chi_Minh",
    )

    return _transform_event(event)


@router.delete("/events/{event_id}")
async def delete_event_handler(
    event_id: str,
    user_id: int = Query(..., description="User ID", gt=0),
    db: Session = Depends(get_db)
):
    """
    Delete a calendar event
    
    - **event_id**: Event ID to delete (path parameter, required)
    """
    # Validate authentication
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)
    
    result = await delete_event(db, user_id, event_id)
    
    return {
        "success": result,
        "message": "Event deleted successfully" if result else "Failed to delete event"
    }