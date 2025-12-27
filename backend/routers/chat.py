from fastapi import APIRouter, Depends
from dependencies.auth import require_auth
from services.ai_service import chat_completion

# 🔒 Dependency ở đây - TẤT CẢ endpoints bên dưới đều cần auth
router = APIRouter(dependencies=[Depends(require_auth)])

@router.post("/")
async def chat(request: dict):
    """Chat endpoint - Tự động protected, không cần check thủ công"""
    message = request.get("message", "")
    reply = await chat_completion(message)
    return {"reply": reply}
