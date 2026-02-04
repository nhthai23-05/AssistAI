from services.ai_service import chat_completion
import json

class ChatService:
    """Service xử lý chat với AI"""
    
    async def send_message(self, message: str, history: list = None):
        try:
            # Build context từ history
            context_str = self._build_context(history or [])
            
            # Tạo full message với context
            full_message = f"{context_str}\n\nUser: {message}" if context_str else message
            
            # Gọi AI service với prompt chat
            response = await chat_completion(
                message=full_message,
                prompt_file="chat.txt"  # chat.txt chưa tối ưu, sẽ build context sau
            )
            
            return {
                'response': response,
                'action': None,
                'data': None
            }
            
        except Exception as e:
            raise Exception(f"Chat error: {str(e)}")
    
    def _build_context(self, history: list) -> str:
        """Build context string từ history"""
        if not history:
            return ""
        
        context_lines = []
        for msg in history[-10:]:  # Lấy 10 tin nhắn gần nhất
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
    
# File này hiện tại đang sử dụng context từ 10 tin nhắn gần nhất --> Không tối ưu context, tốn nhiều chi phí