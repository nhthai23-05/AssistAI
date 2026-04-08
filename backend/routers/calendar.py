from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config.database import get_db
from services.calendar_service import list_events, insert_events, update_events, delete_events
from services.ai_service import smart_event_operation, parse_event_creation, detect_calendar_action
from services.auth_service import has_valid_token

router = APIRouter(tags=["calendar"])

class SmartEventRequest(BaseModel):
    user_request: str

@router.get("/events")
async def get_events(
    user_id: int = Query(..., description="User ID"),
    max_results: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lấy danh sách events từ Google Calendar"""
    try:
        # Check authentication
        if not has_valid_token(db, user_id):
            raise HTTPException(
                status_code=401,
                detail="Not authenticated or token expired"
            )
        
        events = await list_events(db, user_id, max_results)
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/smart-action")
async def smart_action(
    request: SmartEventRequest,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Xử lý calendar action bằng natural language - tự động detect action
    
    Examples:
    - "tạo meeting với team vào 3pm mai"
    - "đổi lịch MBAMC từ 8h sáng thành 1h30 chiều"
    - "hủy meeting với client"
    """
    try:
        # Check authentication
        if not has_valid_token(db, user_id):
            raise HTTPException(
                status_code=401,
                detail="Not authenticated or token expired"
            )
        
        from datetime import datetime
        
        # Bước 1: LLM detect action
        action_result = await detect_calendar_action(request.user_request)
        action = action_result.get("action", "create")
        
        print(f"🤖 Detected action: {action} (confidence: {action_result.get('confidence')})")
        print(f"📝 Reasoning: {action_result.get('reasoning')}")
        
        # Bước 2: Thực hiện action tương ứng
        if action == "create":
            # Lấy events để tránh xung đột
            events = await list_events(db, user_id, max_results=50)
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = await parse_event_creation(request.user_request, current_date, events)
            
            if result.get("error"):
                raise HTTPException(status_code=400, detail=result["error"])
            
            created_event = await insert_events(
                db=db,
                user_id=user_id,
                summary=result["summary"],
                start_datetime=result["start_datetime"],
                end_datetime=result["end_datetime"],
                description=result.get("description"),
                location=result.get("location"),
                attendees=result.get("attendees"),
                recurrence=result.get("recurrence")
            )
            
            return {
                "action": "create",
                "message": "Event created successfully",
                "event": created_event
            }
            
        elif action == "update":
            events = await list_events(db, user_id, max_results=20)
            result = await smart_event_operation(request.user_request, events, operation="update")
            
            if not result.get("event_id"):
                raise HTTPException(status_code=404, detail=result.get("error", "No matching event"))
            
            updates = result["updates"]
            updated_event = await update_events(
                db=db,
                user_id=user_id,
                event_id=result["event_id"],
                summary=updates.get("summary"),
                start_datetime=updates.get("start_datetime"),
                end_datetime=updates.get("end_datetime"),
                description=updates.get("description"),
                location=updates.get("location"),
                attendees=updates.get("attendees")
            )
            
            return {
                "action": "update",
                "message": "Event updated successfully",
                "reasoning": result.get("reasoning"),
                "event": updated_event
            }
            
        elif action == "delete":
            events = await list_events(db, user_id, max_results=20)
            result = await smart_event_operation(request.user_request, events, operation="delete")
            
            if not result.get("event_id"):
                raise HTTPException(status_code=404, detail=result.get("error", "No matching event"))
            
            deleted = await delete_events(db, user_id, result["event_id"])
            
            return {
                "action": "delete",
                "message": "Event deleted successfully",
                "reasoning": result.get("reasoning"),
                "deleted_event": result.get("event_summary"),
                "result": deleted
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/smart-create")
async def smart_create_event(
    request: SmartEventRequest,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Tạo event bằng natural language
    
    Example: "tạo meeting với team vào 3 giờ chiều mai"
    """
    try:
        # Check authentication
        if not has_valid_token(db, user_id):
            raise HTTPException(
                status_code=401,
                detail="Not authenticated or token expired"
            )
        
        from datetime import datetime
        
        # Lấy danh sách events hiện tại để tránh xung đột
        events = await list_events(db, user_id, max_results=50)
        
        # GPT phân tích yêu cầu và tạo cấu trúc dữ liệu
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = await parse_event_creation(request.user_request, current_date, events)
        
        # Kiểm tra lỗi
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Tạo event
        created_event = await insert_events(
            db=db,
            user_id=user_id,
            summary=result["summary"],
            start_datetime=result["start_datetime"],
            end_datetime=result["end_datetime"],
            description=result.get("description"),
            location=result.get("location"),
            attendees=result.get("attendees"),
            recurrence=result.get("recurrence")
        )
        
        return {
            "message": "Event created successfully",
            "event": created_event
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/events/smart-update")
async def smart_update_event(
    request: SmartEventRequest,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Update event bằng natural language
    
    Example: "đổi meeting với client sang 3 giờ chiều mai"
    """
    try:
        # Check authentication
        if not has_valid_token(db, user_id):
            raise HTTPException(
                status_code=401,
                detail="Not authenticated or token expired"
            )
        
        # Lấy danh sách events
        events = await list_events(db, user_id, max_results=20)
        
        # GPT phân tích và chọn event cần update
        result = await smart_event_operation(request.user_request, events, operation="update")
        
        if not result.get("event_id"):
            raise HTTPException(status_code=404, detail=result.get("error", "No matching event"))
        
        # Update event
        updates = result["updates"]
        updated_event = await update_events(
            db=db,
            user_id=user_id,
            event_id=result["event_id"],
            summary=updates.get("summary"),
            start_datetime=updates.get("start_datetime"),
            end_datetime=updates.get("end_datetime"),
            description=updates.get("description"),
            location=updates.get("location"),
            attendees=updates.get("attendees")
        )
        
        return {
            "message": "Event updated successfully",
            "reasoning": result.get("reasoning"),
            "event": updated_event
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/events/smart-delete")
async def smart_delete_event(
    request: SmartEventRequest,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Xóa event bằng natural language
    
    Example: "hủy meeting với client sáng mai"
    """
    try:
        # Check authentication
        if not has_valid_token(db, user_id):
            raise HTTPException(
                status_code=401,
                detail="Not authenticated or token expired"
            )
        
        # Lấy danh sách events
        events = await list_events(db, user_id, max_results=20)
        
        # GPT phân tích và chọn event cần xóa
        result = await smart_event_operation(request.user_request, events, operation="delete")
        
        if not result.get("event_id"):
            raise HTTPException(status_code=404, detail=result.get("error", "No matching event"))
        
        # Xóa event
        deleted = await delete_events(db, user_id, result["event_id"])
        
        return {
            "message": "Event deleted successfully",
            "reasoning": result.get("reasoning"),
            "deleted_event": result.get("event_summary"),
            "result": deleted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))