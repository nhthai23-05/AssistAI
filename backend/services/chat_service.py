"""Chat Service - AI chat with message persistence and intent parsing"""
import json
import logging
import time
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from services.ai_service import parse_user_intent, smart_event_operation, generate_chat_title
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


def _find_invalid_amounts(data) -> bool:
    """Return True if any transaction in data has a non-positive amount."""
    items = data if isinstance(data, list) else [data]
    return any(
        not isinstance(item.get("amount"), (int, float)) or item.get("amount", 0) <= 0
        for item in items
        if isinstance(item, dict)
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
        if not message.strip() and not image_base64:
            raise ValidationError("Message cannot be empty")

        try:
            # Get or create session
            is_new_session = not bool(session_id)
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

            # Fetch categories for tool definitions (best-effort, non-blocking)
            categories: List[str] = []
            income_categories: List[str] = []
            try:
                from config.config import settings
                from services.sheets_service import get_categories as fetch_categories
                from services.sheets_service import get_income_categories as fetch_income_categories
                if settings.google_sheet_id:
                    categories = fetch_categories(db, user_id, settings.google_sheet_id)
                    income_categories = fetch_income_categories(db, user_id, settings.google_sheet_id)
            except Exception:
                pass

            # Parse intent via AI (function calling)
            try:
                intent_result = await parse_user_intent(
                    message=message,
                    categories=categories,
                    income_categories=income_categories,
                    image_base64=image_base64,
                    session_id=session_id,
                )
            except Exception as e:
                raise LLMProcessingError(f"AI processing failed: {str(e)}")

            thinking_ms = int((time.monotonic() - t_start) * 1000)
            tokens_used = intent_result.pop("_tokens", 0)

            # Build response text and actions list
            intent = intent_result.get("intent", "chat")
            data = intent_result.get("data", {})
            logger.info("[intent] user_id=%s session=%s intent=%s confidence=%s data=%s",
                        user_id, session_id, intent,
                        intent_result.get("confidence"), data)
            actions = None

            if intent == "chat":
                response_text = data.get("response", "")

            elif intent == "read_calendar":
                try:
                    from services.calendar_service import list_events as _list_events
                    days_ahead = int(data.get("days_ahead", 30))
                    days_back = int(data.get("days_back", 0))
                    limit = int(data.get("limit", 10))
                    logger.info("[read_calendar] days_ahead=%s days_back=%s limit=%s",
                                days_ahead, days_back, limit)
                    events = await _list_events(
                        db, user_id,
                        max_results=limit,
                        days_ahead=days_ahead,
                        days_back=days_back,
                    )
                    logger.info("[read_calendar] fetched %s events", len(events))
                    if not events:
                        response_text = "Không có sự kiện nào trong khoảng thời gian này."
                    else:
                        from datetime import datetime as _dt
                        lines = ["Đây là lịch của bạn:"]
                        for e in events:
                            start = e.get("start", {})
                            raw_dt = start.get("dateTime", start.get("date", ""))
                            summary = e.get("summary", "Không có tiêu đề")
                            location = e.get("location", "")
                            if "T" in raw_dt:
                                try:
                                    parsed = _dt.fromisoformat(raw_dt.replace("Z", "+00:00"))
                                    dt_str = parsed.strftime("%d/%m %H:%M")
                                except Exception:
                                    dt_str = raw_dt
                            else:
                                dt_str = raw_dt or "Cả ngày"
                            line = f"• {dt_str} — {summary}"
                            if location:
                                line += f" ({location})"
                            lines.append(line)
                        response_text = "\n".join(lines)
                except Exception:
                    response_text = "Xin lỗi, tôi không thể lấy lịch của bạn lúc này."

            elif intent == "read_sheet":
                try:
                    from config.config import settings as _settings
                    from services.sheets_service import read_expenses as _read_expenses
                    if not getattr(_settings, "google_sheet_id", None):
                        response_text = "Chưa cấu hình Google Sheet."
                    else:
                        limit = int(data.get("limit", 50))
                        expenses = _read_expenses(db, user_id, _settings.google_sheet_id, limit=limit)
                        if not expenses:
                            response_text = "Không có khoản chi nào trong khoảng thời gian này."
                        else:
                            total = sum(e.get("amount", 0) for e in expenses)
                            by_cat: Dict[str, float] = {}
                            for e in expenses:
                                cat = e.get("category", "Khác")
                                by_cat[cat] = by_cat.get(cat, 0) + e.get("amount", 0)
                            lines = [f"Tổng {len(expenses)} giao dịch — {total:,.0f} VNĐ:"]
                            for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1]):
                                lines.append(f"• {cat}: {amt:,.0f} VNĐ")
                            response_text = "\n".join(lines)
                except Exception:
                    response_text = "Xin lỗi, tôi không thể đọc dữ liệu thu chi lúc này."

            elif intent == "calendar":
                calendar_action = intent_result.get("action", "create")

                if calendar_action == "create":
                    event_list = data if isinstance(data, list) else [data]
                    count = len(event_list)
                    response_text = (
                        f"Tôi đã phân tích {count} sự kiện. "
                        "Vui lòng xem lại thông tin bên dưới và xác nhận."
                    ) if count > 1 else (
                        "Tôi đã phân tích yêu cầu của bạn. "
                        "Vui lòng xem lại thông tin bên dưới và xác nhận."
                    )
                    actions = [
                        ChatActionData(action_type="create_event", action_status="pending", data=ev)
                        for ev in event_list
                    ]

                elif calendar_action in ("update", "delete"):
                    try:
                        from services.calendar_service import list_events as _list_events
                        events = await _list_events(db, user_id, days_ahead=30, days_back=7)
                        event_query = data.get("event_query", message)
                        op_result = await smart_event_operation(
                            event_query, events, calendar_action, session_id=session_id
                        )
                        if not op_result.get("event_id"):
                            response_text = op_result.get(
                                "error",
                                "Không tìm thấy sự kiện phù hợp. Bạn có thể mô tả rõ hơn không?"
                            )
                        elif calendar_action == "update":
                            updates = {
                                k: v for k, v in (op_result.get("updates") or {}).items()
                                if v is not None
                            }
                            event_id = op_result["event_id"]
                            event_summary = next(
                                (e.get("summary", "") for e in events if e.get("id") == event_id),
                                data.get("summary", ""),
                            )
                            action_data = {"event_id": event_id, "event_summary": event_summary, **updates}
                            response_text = "Tôi sẽ cập nhật sự kiện này. Vui lòng xác nhận."
                            actions = [ChatActionData(action_type="update_event", action_status="pending", data=action_data)]
                        else:
                            matched = next((e for e in events if e.get("id") == op_result["event_id"]), {})
                            start = matched.get("start", {})
                            end = matched.get("end", {})
                            action_data = {
                                "event_id": op_result["event_id"],
                                "event_summary": op_result.get("event_summary", ""),
                                "start_datetime": start.get("dateTime", start.get("date", "")),
                                "end_datetime": end.get("dateTime", end.get("date", "")),
                            }
                            response_text = "Tôi sẽ xóa sự kiện này. Vui lòng xác nhận."
                            actions = [ChatActionData(action_type="delete_event", action_status="pending", data=action_data)]
                    except Exception:
                        response_text = "Không thể xử lý yêu cầu. Vui lòng thử lại."
                else:
                    response_text = (
                        "Tôi đã phân tích yêu cầu của bạn. "
                        "Vui lòng xem lại thông tin bên dưới và xác nhận."
                    )
                    actions = [ChatActionData(action_type="create_event", action_status="pending", data=data)]

            elif intent == "expense":
                invalid = _find_invalid_amounts(data)
                if invalid:
                    response_text = "Số tiền phải là số dương (> 0). Vui lòng nhập lại với số tiền hợp lệ."
                else:
                    count = len(data) if isinstance(data, list) else 1
                    response_text = (
                        f"Tôi đã phân tích {count} khoản chi. "
                        "Vui lòng xem lại thông tin bên dưới và xác nhận."
                    ) if count > 1 else (
                        "Tôi đã phân tích yêu cầu của bạn. "
                        "Vui lòng xem lại thông tin bên dưới và xác nhận."
                    )
                    actions = [ChatActionData(action_type="write_sheet", action_status="pending", data=data)]

            elif intent == "income":
                invalid = _find_invalid_amounts(data)
                if invalid:
                    response_text = "Số tiền phải là số dương (> 0). Vui lòng nhập lại với số tiền hợp lệ."
                else:
                    count = len(data) if isinstance(data, list) else 1
                    response_text = (
                        f"Tôi đã phân tích {count} khoản thu. "
                        "Vui lòng xem lại thông tin bên dưới và xác nhận."
                    ) if count > 1 else (
                        "Tôi đã phân tích yêu cầu của bạn. "
                        "Vui lòng xem lại thông tin bên dưới và xác nhận."
                    )
                    actions = [ChatActionData(action_type="write_income_sheet", action_status="pending", data=data)]

            elif intent == "batch":
                expenses = data.get("expenses", [])
                income_items = data.get("income", [])
                events = data.get("events", [])
                invalid_exp = _find_invalid_amounts(expenses)
                invalid_inc = _find_invalid_amounts(income_items)
                if invalid_exp or invalid_inc:
                    response_text = "Số tiền phải là số dương (> 0). Vui lòng nhập lại với số tiền hợp lệ."
                else:
                    parts = []
                    if expenses:
                        parts.append(f"{len(expenses)} khoản chi")
                    if income_items:
                        parts.append(f"{len(income_items)} khoản thu")
                    if events:
                        parts.append(f"{len(events)} sự kiện")
                    response_text = (
                        "Tôi đã phân tích " + " và ".join(parts) + ". "
                        "Vui lòng xem lại thông tin bên dưới và xác nhận."
                    )
                    actions = []
                    if expenses:
                        actions.append(ChatActionData(
                            action_type="write_sheet", action_status="pending",
                            data=expenses if len(expenses) > 1 else expenses[0],
                        ))
                    if income_items:
                        actions.append(ChatActionData(
                            action_type="write_income_sheet", action_status="pending",
                            data=income_items if len(income_items) > 1 else income_items[0],
                        ))
                    for event in events:
                        actions.append(ChatActionData(
                            action_type="create_event", action_status="pending", data=event,
                        ))

            else:
                response_text = data.get("response", "")

            # Generate title for new chat/read sessions (no action-based label on frontend)
            suggested_title: Optional[str] = None
            if is_new_session and intent in ("chat", "read_calendar", "read_sheet"):
                suggested_title = await generate_chat_title(message) or None
                if suggested_title:
                    session.title = suggested_title

            # Persist user message + assistant response
            try:
                user_msg = Message(
                    session_id=session_id,
                    role=MessageRole.USER,
                    content=message,
                )
                db.add(user_msg)

                actions_json_str = json.dumps([
                    {"action_type": a.action_type, "action_status": a.action_status, "data": a.data}
                    for a in actions
                ]) if actions else None
                assistant_msg = Message(
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=response_text,
                    actions_json=actions_json_str,
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
                "tokens_used": tokens_used,
                "thinking_time_ms": thinking_ms,
                "created_at": assistant_msg.created_at,
                "suggested_title": suggested_title,
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

            result = []
            for msg in reversed(messages):
                entry = {
                    "message_id": msg.message_id,
                    "role": msg.role.value if hasattr(msg.role, "value") else msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                }
                if msg.actions_json:
                    try:
                        entry["actions"] = json.loads(msg.actions_json)
                    except Exception:
                        pass
                result.append(entry)
            return result

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
    def update_action_status(db: Session, user_id: int, message_id: int, action_idx: int, status: str) -> bool:
        """Persist accepted/rejected status for a specific action within a message."""
        try:
            msg = (
                db.query(Message)
                .join(AssistantSession, Message.session_id == AssistantSession.session_id)
                .filter(Message.message_id == message_id, AssistantSession.user_id == user_id)
                .first()
            )
            if not msg or not msg.actions_json:
                return False
            actions = json.loads(msg.actions_json)
            if action_idx < 0 or action_idx >= len(actions):
                return False
            actions[action_idx]["action_status"] = status
            msg.actions_json = json.dumps(actions)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to update action status: {str(e)}")

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
