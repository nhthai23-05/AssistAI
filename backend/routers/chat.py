from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.chat_service import ChatService
from dependencies.auth import require_auth

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
    _=Depends(require_auth)
):
    """
    Gửi message đến AI chatbot
    
    - **message**: Tin nhắn của user
    - **history**: Lịch sử hội thoại (optional)
    """
    try:
        result = await chat_service.send_message(
            message=request.message,
            history=request.history
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))