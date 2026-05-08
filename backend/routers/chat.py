"""Chat Router - Handles chat endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from config.database import get_db
from services.chat_service import ChatService
from services.auth_service import has_valid_token
from schemas.chat import ChatMessageRequest, ChatMessageResponse
from schemas.error import ErrorResponse
from exceptions import (
    NoValidTokenError,
    ValidationError,
)

router = APIRouter(tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    user_id: int = Query(..., description="User ID", gt=0),
    session_id: int = Query(None, description="Session ID (optional)", gt=0),
    db: Session = Depends(get_db)
) -> ChatMessageResponse:
    """
    Send message to AI chatbot
    
    - **message**: User message (required)
    - **history**: Chat history (optional)
    - **user_id**: User ID (required)
    - **session_id**: Session ID (optional)
    """
    # Validate authentication
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)
    
    # Send message and get response
    result = await ChatService.send_message(
        db=db,
        user_id=user_id,
        message=request.message,
        session_id=session_id,
        history=request.history
    )
    
    return ChatMessageResponse(**result)


@router.get("/history")
async def get_message_history(
    session_id: int = Query(..., description="Session ID", gt=0),
    limit: int = Query(10, description="Limit messages", ge=1, le=50),
    user_id: int = Query(..., description="User ID", gt=0),
    db: Session = Depends(get_db)
):
    """
    Get message history for a session
    
    - **session_id**: Session ID (required)
    - **limit**: Max messages to retrieve (default: 10)
    """
    # Validate authentication
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)
    
    history = ChatService.get_message_history(db, session_id, limit)
    return {"session_id": session_id, "messages": history}