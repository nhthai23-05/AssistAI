from fastapi import APIRouter, Depends
from dependencies.auth import require_auth
from services.calendar_service import list_events

# 🔒 Dependency ở đây - TẤT CẢ endpoints bên dưới đều cần auth
router = APIRouter(dependencies=[Depends(require_auth)])

@router.get("/events")
async def get_events(max_results: int = 10):
    """Calendar endpoint - Tự động protected, không cần check thủ công"""
    events = await list_events(max_results)
    return {"events": events}
