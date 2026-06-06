"""AI Service - LLM integration with exception handling"""
import json
from typing import Dict, List, Optional, Any
import openai
from openai import OpenAI
from config.config import settings
from services.token_usage_service import TokenUsageService
from exceptions import (
    LLMProcessingError,
    DatabaseError,
)

token_usage_service = TokenUsageService()
openai_client = OpenAI(api_key=settings.llm_api_key)


async def smart_event_operation(
    user_request: str,
    events_list: List[Dict],
    operation: str = "update",
    session_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Match user's natural language request to an existing calendar event using function calling.

    Returns dict with event_id and updates (for update) or event_summary (for delete).
    event_id is None when no matching event is found.
    """
    events_text = "\n".join([
        f"ID: {e.get('id')} | {e.get('summary', 'No title')} | "
        f"Start: {e.get('start', {}).get('dateTime', e.get('start', {}).get('date', 'N/A'))}"
        for e in events_list
    ])

    system_prompt = (
        f"You have the following calendar events:\n{events_text}\n\n"
        f"The user wants to {operation} one of these events. "
        "Call the function to indicate which event and what to change. "
        "If no event matches, use event_id=null."
    )

    if operation == "update":
        tools = [{
            "type": "function",
            "function": {
                "name": "select_event_to_update",
                "description": "Select which event to update and specify the changes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string", "description": "ID of the event, or null if not found"},
                        "updates": {
                            "type": "object",
                            "description": "Fields to update (omit unchanged fields)",
                            "properties": {
                                "summary": {"type": "string"},
                                "start_datetime": {"type": "string", "description": "ISO 8601 with +07:00"},
                                "end_datetime": {"type": "string", "description": "ISO 8601 with +07:00"},
                                "description": {"type": "string"},
                                "location": {"type": "string"},
                            },
                        },
                    },
                    "required": ["event_id", "updates"],
                },
            },
        }]
        tool_choice = {"type": "function", "function": {"name": "select_event_to_update"}}
    else:
        tools = [{
            "type": "function",
            "function": {
                "name": "select_event_to_delete",
                "description": "Select which event to delete.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string", "description": "ID of the event, or null if not found"},
                        "event_summary": {"type": "string", "description": "Event title for confirmation"},
                    },
                    "required": ["event_id", "event_summary"],
                },
            },
        }]
        tool_choice = {"type": "function", "function": {"name": "select_event_to_delete"}}

    try:
        response = openai_client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request},
            ],
            tools=tools,
            tool_choice=tool_choice,
            max_completion_tokens=settings.llm_max_tokens,
        )
    except openai.APIConnectionError as e:
        raise LLMProcessingError(f"Could not connect to OpenAI: {str(e)}")
    except openai.RateLimitError as e:
        raise LLMProcessingError(f"OpenAI rate limit exceeded: {str(e)}")
    except openai.APIStatusError as e:
        raise LLMProcessingError(f"OpenAI API error {e.status_code}: {e.message}")

    if response.usage and session_id:
        try:
            await token_usage_service.log_token_usage(
                session_id=session_id,
                usage_type="llm_api",
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens or 0,
                model=settings.llm_model,
            )
        except DatabaseError:
            pass

    msg = response.choices[0].message
    if not msg.tool_calls:
        return {"event_id": None, "error": "No matching event found"}

    try:
        return json.loads(msg.tool_calls[0].function.arguments)
    except json.JSONDecodeError as e:
        raise LLMProcessingError(f"Failed to parse event selection response: {str(e)}")


async def generate_chat_title(message: str) -> str:
    """Generate a short 3-5 word Vietnamese title summarising the user's first message."""
    try:
        response = openai_client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tóm tắt tin nhắn sau thành tiêu đề ngắn 3-5 từ bằng tiếng Việt. "
                        "Chỉ trả về tiêu đề, không dấu ngoặc kép, không dấu chấm cuối."
                    ),
                },
                {"role": "user", "content": message[:500]},
            ],
            max_completion_tokens=15,
        )
        return response.choices[0].message.content.strip().strip('"\'.,')
    except Exception:
        return ""


def _tool_call_to_intent(name: str, args: Dict[str, Any], tokens: int) -> Dict[str, Any]:
    base: Dict[str, Any] = {"confidence": 0.95, "_tokens": tokens}

    if name == "add_expense":
        txns = args.get("transactions", [])
        return {**base, "intent": "expense", "data": txns[0] if len(txns) == 1 else txns}

    if name == "add_income":
        txns = args.get("transactions", [])
        return {**base, "intent": "income", "data": txns[0] if len(txns) == 1 else txns}

    if name == "create_calendar_event":
        evts = args.get("events", [])
        return {**base, "intent": "calendar", "action": "create", "data": evts[0] if len(evts) == 1 else evts}

    if name == "update_calendar_event":
        return {**base, "intent": "calendar", "action": "update", "data": args}

    if name == "delete_calendar_event":
        return {**base, "intent": "calendar", "action": "delete", "data": args}

    if name == "read_calendar":
        args.setdefault("limit", 10)
        args.setdefault("query", "")
        return {**base, "intent": "read_calendar", "data": args}

    if name == "read_sheet":
        args.setdefault("limit", 50)
        args.setdefault("query", "")
        return {**base, "intent": "read_sheet", "data": args}

    return {"intent": "chat", "confidence": 0.5, "data": {"response": ""}, "_tokens": tokens}


async def parse_user_intent(
    message: str,
    categories: Optional[List[str]] = None,
    income_categories: Optional[List[str]] = None,
    image_base64: Optional[str] = None,
    session_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Classify user message using OpenAI function calling.

    Returns dict with intent, action (calendar only), data, _tokens.
    When no tool is called, returns chat intent with the model's text reply.

    Raises:
        LLMProcessingError: If OpenAI API call fails
    """
    from datetime import datetime

    current_date = datetime.now().strftime("%Y-%m-%d")
    expense_cats = categories or ["Ăn uống", "Di chuyển", "Mua sắm", "Giải trí", "Khác"]
    income_cats = income_categories or ["Lương", "Thưởng", "Freelance", "Khác"]

    system_prompt = (
        f"You are an AI assistant helping users track expenses, income, and calendar events. "
        f"Current date: {current_date}. "
        "Amounts in VND: '50k'=50000, '1 triệu'=1000000, '2.5m'=2500000. "
        "Date defaults to today when not mentioned. "
        "Expense = money spent/paid; Income = money received (salary, bonus, freelance). "
        "For receipt images → add_expense (extract store name, total, date). "
        "For calendar images/posters → create_calendar_event. "
        "Calendar routing — follow strictly: "
        "xóa/hủy/bỏ/cancel + event name → delete_calendar_event (NEVER read_calendar). "
        "sửa/đổi/dời/cập nhật/reschedule + event name → update_calendar_event (NEVER read_calendar). "
        "thêm/tạo/đặt lịch + details → create_calendar_event. "
        "xem/kiểm tra/có gì/lịch hôm nay (no delete/update intent) → read_calendar. "
        "Respond in Vietnamese when no tool is called."
    )

    def _cat_prop(cats: List[str]) -> Dict[str, Any]:
        p: Dict[str, Any] = {"type": "string"}
        if cats:
            p["enum"] = cats
        return p

    def _transaction_item(cats: List[str]) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date YYYY-MM-DD"},
                "amount": {"type": "number", "description": "Amount in VND"},
                "description": {"type": "string"},
                "category": {**_cat_prop(cats), "description": "Matching category"},
            },
            "required": ["date", "amount", "description", "category"],
        }

    tools = [
        {
            "type": "function",
            "function": {
                "name": "add_expense",
                "description": "Record expense transaction(s) — money the user SPENT or PAID (purchases, bills, food, etc.).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transactions": {
                            "type": "array",
                            "items": _transaction_item(expense_cats),
                            "description": "One or more expense transactions",
                        }
                    },
                    "required": ["transactions"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "add_income",
                "description": "Record income transaction(s) — money the user RECEIVED or EARNED (salary, bonus, freelance, etc.).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transactions": {
                            "type": "array",
                            "items": _transaction_item(income_cats),
                            "description": "One or more income transactions",
                        }
                    },
                    "required": ["transactions"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_calendar_event",
                "description": "Create one or more new calendar events/appointments.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "summary": {"type": "string", "description": "Event title"},
                                    "start_datetime": {"type": "string", "description": "ISO datetime YYYY-MM-DDTHH:MM:SS"},
                                    "end_datetime": {"type": "string", "description": "ISO datetime, default 1 hour after start"},
                                    "description": {"type": "string"},
                                    "location": {"type": "string"},
                                },
                                "required": ["summary", "start_datetime", "end_datetime"],
                            },
                        }
                    },
                    "required": ["events"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_calendar_event",
                "description": "Update/modify/reschedule an existing calendar event. Triggered by: sửa, đổi, dời, cập nhật, thay đổi, reschedule + event name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_query": {"type": "string", "description": "Natural language description of which event to update"},
                        "changes": {
                            "type": "object",
                            "description": "Fields to update (only changed fields)",
                            "properties": {
                                "summary": {"type": "string"},
                                "start_datetime": {"type": "string"},
                                "end_datetime": {"type": "string"},
                                "location": {"type": "string"},
                                "description": {"type": "string"},
                            },
                        },
                    },
                    "required": ["event_query", "changes"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "delete_calendar_event",
                "description": "Delete/cancel/remove an existing calendar event. Triggered by: xóa, hủy, bỏ, cancel, remove + event name. Do NOT use read_calendar first.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_query": {"type": "string", "description": "Natural language description of which event to delete"}
                    },
                    "required": ["event_query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_calendar",
                "description": "View/list upcoming or past events. Use ONLY when user wants to SEE their schedule (e.g. 'tuần tới có gì', 'hôm nay có lịch gì', 'xem lịch'). Do NOT use when user wants to delete, cancel, update, or modify an event.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "days_ahead": {"type": "integer", "description": "Days ahead to look (0 for past-only)"},
                        "days_back": {"type": "integer", "description": "Days back to look (0 for future-only)"},
                        "limit": {"type": "integer", "description": "Max events to return (default 10)"},
                        "query": {"type": "string", "description": "Original query phrase"},
                    },
                    "required": ["days_ahead", "days_back"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_sheet",
                "description": "View expense/income history or spending summary. Use when user asks ABOUT past transactions (e.g. 'tháng này chi bao nhiêu', 'xem lịch sử').",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max rows to return (default 50)"},
                        "query": {"type": "string", "description": "Original query phrase"},
                    },
                    "required": [],
                },
            },
        },
    ]

    user_content: Any
    if image_base64:
        user_content = [
            {"type": "text", "text": message or "Phân tích ảnh này."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
        ]
    else:
        user_content = message

    try:
        response = openai_client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            tools=tools,
            tool_choice="auto",
            max_completion_tokens=settings.llm_max_tokens,
        )
    except openai.APIConnectionError as e:
        raise LLMProcessingError(f"Could not connect to OpenAI: {str(e)}")
    except openai.RateLimitError as e:
        raise LLMProcessingError(f"OpenAI rate limit exceeded: {str(e)}")
    except openai.APIStatusError as e:
        raise LLMProcessingError(f"OpenAI API error {e.status_code}: {e.message}")

    tokens = 0
    if response.usage:
        tokens = response.usage.total_tokens or 0
        if session_id:
            try:
                await token_usage_service.log_token_usage(
                    session_id=session_id,
                    usage_type="llm_api",
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=tokens,
                    model=settings.llm_model,
                )
            except DatabaseError:
                pass

    msg = response.choices[0].message

    if not msg.tool_calls:
        return {
            "intent": "chat",
            "confidence": 0.0,
            "data": {"response": "Xin lỗi, tôi không hiểu ý định của bạn. Bạn có thể mô tả rõ hơn không?"},
            "_tokens": tokens,
        }

    if len(msg.tool_calls) > 1:
        expenses: List[Dict] = []
        income: List[Dict] = []
        events: List[Dict] = []
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            if tc.function.name == "add_expense":
                expenses.extend(args.get("transactions", []))
            elif tc.function.name == "add_income":
                income.extend(args.get("transactions", []))
            elif tc.function.name == "create_calendar_event":
                events.extend(args.get("events", []))
        return {
            "intent": "batch",
            "confidence": 0.95,
            "data": {"expenses": expenses, "income": income, "events": events},
            "_tokens": tokens,
        }

    tc = msg.tool_calls[0]
    try:
        args = json.loads(tc.function.arguments)
    except json.JSONDecodeError:
        args = {}
    return _tool_call_to_intent(tc.function.name, args, tokens)
