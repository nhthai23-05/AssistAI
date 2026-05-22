"""Chat Router - Handles chat and session endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from config.database import get_db
from services.chat_service import ChatService
from services.auth_service import has_valid_token
from schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatSessionSummary
from exceptions import NoValidTokenError

router = APIRouter(tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    user_id: int = Query(..., description="User ID", gt=0),
    db: Session = Depends(get_db),
) -> ChatMessageResponse:
    """Send a message (text + optional image) to the AI assistant."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    result = await ChatService.send_message(
        db=db,
        user_id=user_id,
        message=request.message,
        session_id=request.session_id,
        image_base64=request.image_base64,
    )
    return ChatMessageResponse(**result)


@router.get("/history")
async def get_message_history(
    session_id: int = Query(..., description="Session ID", gt=0),
    limit: int = Query(10, description="Max messages", ge=1, le=50),
    user_id: int = Query(..., description="User ID", gt=0),
    db: Session = Depends(get_db),
):
    """Return message history for a session."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    history = ChatService.get_message_history(db, session_id, limit)
    return {"session_id": session_id, "messages": history}


# --- Session management ---

@router.post("/sessions")
async def create_session(
    user_id: int = Query(..., description="User ID", gt=0),
    title: str = Query(None, description="Session title (optional)"),
    db: Session = Depends(get_db),
):
    """Create a new chat session."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    session = ChatService.create_session(db, user_id, title=title)
    return {"session_id": session.session_id, "created_at": session.created_at}


@router.get("/sessions", response_model=List[ChatSessionSummary])
async def list_sessions(
    user_id: int = Query(..., description="User ID", gt=0),
    limit: int = Query(20, description="Max sessions", ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List active sessions for a user, most recent first."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sessions = ChatService.list_sessions(db, user_id, limit)
    return [ChatSessionSummary(**s) for s in sessions]


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    user_id: int = Query(..., description="User ID", gt=0),
    db: Session = Depends(get_db),
):
    """Soft-delete a session (set status=cancelled)."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    ChatService.delete_session(db, user_id, session_id)
    return {"success": True, "session_id": session_id}
