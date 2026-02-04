import requests
from config import API

class ChatService:
    """Service để gọi chat API"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/chat"
    
    def send_message(self, message: str, conversation_history: list = None):
        """
        Gửi message đến AI
        
        Args:
            message: User message
            conversation_history: Lịch sử chat
            
        Returns:
            dict: {'response': str, 'action': str, 'data': dict}
        """
        try:
            payload = {
                'message': message,
                'history': conversation_history or []
            }
            
            response = requests.post(
                f"{self.base_url}/message",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Chat API error: {str(e)}")