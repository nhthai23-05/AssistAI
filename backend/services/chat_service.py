"""Chat Service - AI chat with message persistence and intent parsing"""
import time
from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from services.ai_service import parse_user_intent
from models.message import Message, MessageRole
from models.assistant_session import AssistantSession, SessionStatus
from models.workspace import Workspace, WorkspaceStatus
from schemas.chat import ChatActionData
from exceptions import (
    SessionNotFoundError,
    LLMProcessingError,
    DatabaseError,
    ValidationError,
)


class ChatService:

    @staticmethod
    def get_or_create_workspace(db: Session, user_id: int) -> int:
        """Return user's first active workspace ID, creating a default one if needed."""
        workspace = (
            db.query(Workspace)
            .filter(
                Workspace.owner_user_id == user_id,
                Workspace.status == WorkspaceStatus.ACTIVE,
            )
            .first()
        )
        if workspace:
            return workspace.workspace_id

        workspace = Workspace(
            owner_user_id=user_id,
            name="Personal",
            status=WorkspaceStatus.ACTIVE,
        )
        db.add(workspace)
        db.flush()
        return workspace.workspace_id

    @staticmethod
    def create_session(db: Session, user_id: int, title: Optional[str] = None) -> AssistantSession:
        """Create a new chat session for the user."""
        try:
            workspace_id = ChatService.get_or_create_workspace(db, user_id)
            session = AssistantSession(
                user_id=user_id,
                workspace_id=workspace_id,
                title=title,
                status=SessionStatus.ACTIVE,
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to create session: {str(e)}")

    @staticmethod
    async def send_message(
        db: Session,
        user_id: int,
        message: str,
        session_id: Optional[int] = None,
        image_base64: Optional[str] = None,
        history: Optional[List] = None,
    ) -> Dict:
        """
        Send message to AI, persist to DB, return structured response.

        Raises:
            ValidationError: If message is empty
            SessionNotFoundError: If given session_id does not exist
            LLMProcessingError: If AI call fails
            DatabaseError: If DB write fails
        """
        if not message or not message.strip():
            raise ValidationError("Message cannot be empty")

        try:
            # Get or create session
            if session_id:
                session = db.query(AssistantSession).filter(
                    AssistantSession.session_id == session_id,
                    AssistantSession.user_id == user_id,
                ).first()
                if not session:
                    raise SessionNotFoundError(session_id=session_id)
            else:
                session = ChatService.create_session(db, user_id)
                session_id = session.session_id

            t_start = time.monotonic()

            # Fetch categories for intent parsing (best-effort, non-blocking)
            categories: List[str] = []
            try:
                from config.config import settings
                from services.sheets_service import get_categories as fetch_categories
                if settings.google_sheet_id:
                    categories = fetch_categories(db, user_id, settings.google_sheet_id)
            except Exception:
                pass

            # Parse intent via AI
            try:
                intent_result = await parse_user_intent(
                    message=message,
                    categories=categories,
                    image_base64=image_base64,
                    session_id=session_id,
                )
            except Exception as e:
                raise LLMProcessingError(f"AI processing failed: {str(e)}")

            thinking_ms = int((time.monotonic() - t_start) * 1000)

            # Build response text and actions list
            intent = intent_result.get("intent", "chat")
            data = intent_result.get("data", {})

            if intent == "chat":
                response_text = data.get("response", "")
                actions = None
            else:
                response_text = (
                    "Tôi đã phân tích yêu cầu của bạn. "
                    "Vui lòng xem lại thông tin bên dưới và xác nhận."
                )
                actions = [
                    ChatActionData(
                        action_type=intent,
                        action_status="pending",
                        data=data,
                    )
                ]

            # Persist user message + assistant response
            try:
                user_msg = Message(
                    session_id=session_id,
                    role=MessageRole.USER,
                    content=message,
                )
                db.add(user_msg)

                assistant_msg = Message(
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=response_text,
                )
                db.add(assistant_msg)
                db.commit()
                db.refresh(assistant_msg)
            except Exception as e:
                db.rollback()
                raise DatabaseError(f"Failed to persist messages: {str(e)}")

            return {
                "message_id": assistant_msg.message_id,
                "session_id": session_id,
                "response": response_text,
                "actions": actions,
                "tokens_used": 0,
                "thinking_time_ms": thinking_ms,
                "created_at": assistant_msg.created_at,
            }

        except (ValidationError, SessionNotFoundError, LLMProcessingError, DatabaseError):
            raise
        except Exception as e:
            raise LLMProcessingError(f"Chat error: {str(e)}")

    @staticmethod
    def _build_context(history: List) -> str:
        if not history:
            return ""
        lines = []
        for msg in history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines)

    @staticmethod
    def get_message_history(db: Session, session_id: int, limit: int = 10) -> List[Dict]:
        """Return message history for a session, oldest first."""
        try:
            session = db.query(AssistantSession).filter(
                AssistantSession.session_id == session_id
            ).first()
            if not session:
                raise SessionNotFoundError(session_id=session_id)

            messages = (
                db.query(Message)
                .filter(Message.session_id == session_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "role": msg.role.value if hasattr(msg.role, "value") else msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                }
                for msg in reversed(messages)
            ]

        except SessionNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to get message history: {str(e)}")

    @staticmethod
    def list_sessions(db: Session, user_id: int, limit: int = 20) -> List[Dict]:
        """Return non-cancelled sessions for a user, most recent first."""
        try:
            sessions = (
                db.query(AssistantSession)
                .filter(
                    AssistantSession.user_id == user_id,
                    AssistantSession.status != SessionStatus.CANCELLED,
                )
                .order_by(AssistantSession.updated_at.desc())
                .limit(limit)
                .all()
            )

            result = []
            for s in sessions:
                msg_count = db.query(Message).filter(Message.session_id == s.session_id).count()
                last_msg = (
                    db.query(Message)
                    .filter(Message.session_id == s.session_id)
                    .order_by(Message.created_at.desc())
                    .first()
                )
                result.append({
                    "session_id": s.session_id,
                    "title": s.title,
                    "message_count": msg_count,
                    "last_message_at": last_msg.created_at if last_msg else s.created_at,
                    "total_tokens_used": 0,
                    "status": s.status.value if hasattr(s.status, "value") else s.status,
                })
            return result
        except Exception as e:
            raise DatabaseError(f"Failed to list sessions: {str(e)}")

    @staticmethod
    def delete_session(db: Session, user_id: int, session_id: int) -> bool:
        """Soft-delete a session by setting status=CANCELLED."""
        try:
            session = db.query(AssistantSession).filter(
                AssistantSession.session_id == session_id,
                AssistantSession.user_id == user_id,
            ).first()
            if not session:
                raise SessionNotFoundError(session_id=session_id)

            session.status = SessionStatus.CANCELLED
            db.commit()
            return True
        except SessionNotFoundError:
            raise
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to delete session: {str(e)}")
