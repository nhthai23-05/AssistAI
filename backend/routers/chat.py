from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from config.database import get_db
from services.chat_service import ChatService
from services.auth_service import has_valid_token

router = APIRouter(tags=["chat"])
chat_service = ChatService()

class ChatRequest(BaseModel):
    message: str
    history: list = []

class ChatResponse(BaseModel):
    response: str
    action: Optional[str] = None
    data: Optional[dict] = None

@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Gửi message đến AI chatbot
    
    - **message**: Tin nhắn của user
    - **history**: Lịch sử hội thoại (optional)
    - **user_id**: User ID (required)
    """
    try:
        # Check authentication
        if not has_valid_token(db, user_id):
            raise HTTPException(
                status_code=401,
                detail="Not authenticated or token expired"
            )
        
        result = await chat_service.send_message(
            message=request.message,
            history=request.history,
            user_id=user_id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))