"""Chat Service - Handles AI chat with message persistence"""
from services.ai_service import chat_completion
from services.token_usage_service import TokenUsageService
from sqlalchemy.orm import Session
from models.message import Message
from models.assistant_session import AssistantSession
from typing import Optional, Dict, List
from datetime import datetime
from exceptions import (
    SessionNotFoundError,
    LLMProcessingError,
    DatabaseError,
    ValidationError,
)


class ChatService:
    """Service for handling chat with AI and message persistence"""
    
    @staticmethod
    async def send_message(
        db: Session,
        user_id: int,
        message: str,
        session_id: Optional[int] = None,
        history: Optional[List] = None,
    ) -> Dict:
        """
        Send message to AI chatbot and persist to database
        
        Args:
            db: Database session
            user_id: User ID (for audit)
            message: User message
            session_id: Session ID (optional, will create new if not provided)
            history: Chat history (optional, used for context)
            
        Returns:
            Dict with response, action, and data
            
        Raises:
            ValidationError: If message is empty
            SessionNotFoundError: If session not found
            LLMProcessingError: If AI processing fails
            DatabaseError: If database operation fails
        """
        if not message or not message.strip():
            raise ValidationError("Message cannot be empty")
        
        try:
            # Get or validate session
            if session_id:
                session = db.query(AssistantSession).filter(
                    AssistantSession.session_id == session_id,
                    AssistantSession.user_id == user_id
                ).first()
                if not session:
                    raise SessionNotFoundError(session_id=session_id)
            
            # Build context from history
            context_str = ChatService._build_context(history or [])
            full_message = f"{context_str}\n\nUser: {message}" if context_str else message
            
            # Call AI service
            try:
                response = await chat_completion(
                    message=full_message,
                    prompt_file="chat.txt",
                    session_id=session_id,
                    user_id=user_id
                )
            except Exception as e:
                raise LLMProcessingError(f"AI processing failed: {str(e)}")
            
            # Persist user message to database
            try:
                user_msg = Message(
                    session_id=session_id,
                    user_id=user_id,
                    content=message,
                    role="user",
                    created_at=datetime.utcnow()
                )
                db.add(user_msg)
                
                # Persist assistant response
                assistant_msg = Message(
                    session_id=session_id,
                    user_id=user_id,
                    content=response.get('response', ''),
                    role="assistant",
                    created_at=datetime.utcnow()
                )
                db.add(assistant_msg)
                db.commit()
                
            except Exception as e:
                db.rollback()
                raise DatabaseError(f"Failed to persist messages: {str(e)}")
            
            # Log token usage if available
            if response.get('usage'):
                try:
                    await TokenUsageService.log_token_usage(
                        session_id=session_id,
                        usage_type="llm_api",
                        prompt_tokens=response['usage'].get('prompt_tokens', 0),
                        completion_tokens=response['usage'].get('completion_tokens', 0),
                        total_tokens=response['usage'].get('total_tokens', 0),
                        db=db
                    )
                except Exception:
                    pass  # Don't fail if token logging fails
            
            return {
                'response': response.get('response', ''),
                'action': response.get('action'),
                'data': response.get('data'),
                'message_id': assistant_msg.message_id if session_id else None
            }
            
        except (ValidationError, SessionNotFoundError, LLMProcessingError, DatabaseError):
            raise
        except Exception as e:
            raise LLMProcessingError(f"Chat error: {str(e)}")
    
    @staticmethod
    def _build_context(history: List) -> str:
        """
        Build context string from message history
        
        Args:
            history: List of message dicts with 'role' and 'content' keys
            
        Returns:
            Context string
        """
        if not history:
            return ""
        
        context_lines = []
        for msg in history[-10:]:  # Use last 10 messages
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if content:
                context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
    
    @staticmethod
    def get_message_history(
        db: Session,
        session_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get message history for a session
        
        Args:
            db: Database session
            session_id: Session ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dicts
            
        Raises:
            SessionNotFoundError: If session not found
            DatabaseError: If database operation fails
        """
        try:
            # Verify session exists
            session = db.query(AssistantSession).filter(
                AssistantSession.session_id == session_id
            ).first()
            if not session:
                raise SessionNotFoundError(session_id=session_id)
            
            # Get messages
            messages = db.query(Message).filter(
                Message.session_id == session_id
            ).order_by(Message.created_at.desc()).limit(limit).all()
            
            return [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in reversed(messages)
            ]
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to get message history: {str(e)}")