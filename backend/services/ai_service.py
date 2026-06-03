"""AI Service - LLM integration with exception handling"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import openai
from openai import OpenAI
from config.config import settings
from services.token_usage_service import TokenUsageService
from exceptions import (
    LLMProcessingError,
    JSONParseError,
    ActionDetectionError,
    DatabaseError,
)

PROMPT_PATH = Path(__file__).parent.parent / "prompt"
token_usage_service = TokenUsageService()
openai_client = OpenAI(api_key=settings.llm_api_key)


def _extract_json(text: str) -> str:
    """
    Extract JSON from LLM response (may be wrapped in markdown code block)
    
    Raises:
        JSONParseError: If no valid JSON found in response
    """
    # Remove markdown code block if present
    if "```json" in text:
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
    elif "```" in text:
        match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
    
    # Find first JSON object
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    
    raise JSONParseError(f"No valid JSON found in response: {text[:100]}...")


async def chat_completion(
    message: str,
    prompt_file: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[int] = None,
    user_id: Optional[int] = None,
    image_base64: Optional[str] = None,
) -> str:
    """
    Call OpenAI API with optional prompt template
    
    Args:
        message: User message
        prompt_file: Prompt template filename in prompt/ directory
        context: Dict of variables to substitute in template
        session_id: Session ID for token tracking
        user_id: User ID for context
    
    Returns:
        LLM response text
    
    Raises:
        LLMProcessingError: If OpenAI API call fails
        JSONParseError: If response parsing fails (if JSON extraction needed)
        DatabaseError: If token logging fails
    """
    try:
        # Build full message with prompt template if provided
        if prompt_file:
            prompt_path = PROMPT_PATH / prompt_file
            if prompt_path.exists():
                prompt_template = prompt_path.read_text(encoding='utf-8')
                
                # Substitute context variables in template
                if context:
                    for key, value in context.items():
                        prompt_template = prompt_template.replace(f"{{{key}}}", str(value))
                
                full_message = f"{prompt_template}\n\nUser input: {message}"
            else:
                full_message = message
        else:
            full_message = message
        
        # Build message content (text only or text + image)
        if image_base64:
            user_content: Any = [
                {"type": "text", "text": full_message},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ]
        else:
            user_content = full_message

        # Call OpenAI API
        try:
            response = openai_client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": user_content}],
                max_completion_tokens=settings.llm_max_tokens,
            )
        except openai.APIConnectionError as e:
            raise LLMProcessingError(f"Could not connect to OpenAI: {str(e)}")
        except openai.RateLimitError as e:
            raise LLMProcessingError(f"OpenAI rate limit exceeded: {str(e)}")
        except openai.APIStatusError as e:
            raise LLMProcessingError(f"OpenAI API error {e.status_code}: {e.message}")
        
        # Extract response content
        if not response.choices or not response.choices[0].message.content:
            raise LLMProcessingError("OpenAI returned empty response")
        
        result = response.choices[0].message.content.strip()
        
        # Log token usage if session_id provided
        if session_id and hasattr(response, 'usage') and response.usage:
            try:
                await token_usage_service.log_token_usage(
                    session_id=session_id,
                    usage_type="llm_api",
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                    model=settings.llm_model,
                )
            except DatabaseError:
                # Token logging failure should not block main operation
                pass
        
        return result
    
    except (LLMProcessingError, JSONParseError, DatabaseError):
        raise
    except Exception as e:
        raise LLMProcessingError(f"Unexpected error in chat_completion: {str(e)}")

async def parse_event_creation(
    user_request: str,
    current_date: Optional[str] = None,
    events_list: Optional[List[Dict]] = None,
    session_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Parse user request into event creation structure
    
    Args:
        user_request: User request (e.g., "create meeting with team at 3pm tomorrow")
        current_date: Current date for LLM context
        events_list: Existing events to avoid conflicts
        session_id: Session ID for token tracking
    
    Returns:
        Dict with event creation parameters:
            - summary: Event title
            - start_datetime: Start time ISO format
            - end_datetime: End time ISO format
            - description: (optional) Event description
            - location: (optional) Event location
            - attendees: (optional) List of attendee emails
            - recurrence: (optional) RRULE list
    
    Raises:
        LLMProcessingError: If LLM call fails
        JSONParseError: If response is not valid JSON
    """
    try:
        from datetime import datetime
        
        if not current_date:
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format events list if provided
        if events_list:
            events_text = "\n".join([
                f"- {event.get('summary', 'No title')}: "
                f"{event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'N/A'))} → "
                f"{event.get('end', {}).get('dateTime', event.get('end', {}).get('date', 'N/A'))}"
                for event in events_list
            ])
        else:
            events_text = "No events this week"
        
        context = {
            "request": user_request,
            "current_date": current_date,
            "events": events_text,
        }
        
        response = await chat_completion(
            message=user_request,
            prompt_file="create_event.txt",
            context=context,
            session_id=session_id,
        )
        
        # Parse JSON response
        try:
            json_str = _extract_json(response)
            result = json.loads(json_str)
        except JSONParseError:
            raise
        except json.JSONDecodeError as e:
            raise JSONParseError(f"Invalid JSON in LLM response: {str(e)}")
        
        return result
    
    except (LLMProcessingError, JSONParseError):
        raise
    except Exception as e:
        raise LLMProcessingError(f"Event parsing failed: {str(e)}")


async def detect_calendar_action(
    user_request: str,
    session_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Detect calendar action type from user request
    
    Args:
        user_request: User request
        session_id: Session ID for token tracking
    
    Returns:
        Dict with:
            - action: "create", "update", or "delete"
            - confidence: Float 0-1
            - reasoning: Explanation of detected action
    
    Raises:
        ActionDetectionError: If action detection fails
    """
    try:
        context = {"request": user_request}
        
        response = await chat_completion(
            message=user_request,
            prompt_file="detect_action.txt",
            context=context,
            session_id=session_id,
        )
        
        # Parse JSON response
        try:
            json_str = _extract_json(response)
            result = json.loads(json_str)
        except (JSONParseError, json.JSONDecodeError) as e:
            raise ActionDetectionError(f"Failed to parse action detection response: {str(e)}")
        
        # Validate required fields
        if "action" not in result:
            raise ActionDetectionError("Response missing 'action' field")
        
        # Set defaults for optional fields
        result.setdefault("confidence", 0.8)
        result.setdefault("reasoning", "Action detected from user request")
        
        return result
    
    except (ActionDetectionError, LLMProcessingError):
        raise
    except Exception as e:
        raise ActionDetectionError(f"Action detection failed: {str(e)}")


async def smart_event_operation(
    user_request: str,
    events_list: List[Dict],
    operation: str = "update",
    session_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Perform smart calendar operation (update/delete based on natural language)
    
    Args:
        user_request: User request (e.g., "change meeting to 2pm")
        events_list: List of existing events
        operation: "update" or "delete"
        session_id: Session ID for token tracking
    
    Returns:
        Dict with:
            - event_id: ID of matched event
            - updates: (for update) Dict of changes
            - event_summary: Event name/summary
            - reasoning: Explanation of action
    
    Raises:
        LLMProcessingError: If LLM call fails
        JSONParseError: If response is not valid JSON
    """
    try:
        # Format events list
        events_text = "\n".join([
            f"ID: {event.get('id')}\n"
            f"Title: {event.get('summary')}\n"
            f"Start: {event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))}\n"
            f"End: {event.get('end', {}).get('dateTime', event.get('end', {}).get('date'))}\n"
            f"Location: {event.get('location', 'N/A')}\n"
            for event in events_list
        ])
        
        context = {
            "events": events_text,
            "request": user_request,
            "operation": operation,
        }
        
        # Choose prompt file
        prompt_file = "choose_events.txt" if operation == "update" else "delete_event.txt"
        
        response = await chat_completion(
            message=user_request,
            prompt_file=prompt_file,
            context=context,
            session_id=session_id,
        )
        
        # Parse JSON response
        try:
            json_str = _extract_json(response)
            result = json.loads(json_str)
        except (JSONParseError, json.JSONDecodeError) as e:
            raise JSONParseError(f"Invalid JSON in event operation response: {str(e)}")
        
        return result
    
    except (LLMProcessingError, JSONParseError):
        raise
    except Exception as e:
        raise LLMProcessingError(f"Smart event operation failed: {str(e)}")


async def parse_user_intent(
    message: str,
    categories: Optional[List[str]] = None,
    image_base64: Optional[str] = None,
    session_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Classify user message into expense, calendar, or chat intent.

    Returns dict with keys: intent, confidence, data.
    Falls back to chat intent when confidence < 0.65.

    Raises:
        LLMProcessingError: If AI call fails
        JSONParseError: If response is not parseable JSON
    """
    from datetime import datetime

    current_date = datetime.now().strftime("%Y-%m-%d")
    categories_str = ", ".join(categories) if categories else "Ăn uống, Di chuyển, Mua sắm, Giải trí, Khác"

    context = {
        "current_date": current_date,
        "categories": categories_str,
        "message": message,
    }

    try:
        response = await chat_completion(
            message=message,
            prompt_file="parse_intent.txt",
            context=context,
            session_id=session_id,
            image_base64=image_base64,
        )

        try:
            json_str = _extract_json(response)
            result = json.loads(json_str)
        except (JSONParseError, json.JSONDecodeError) as e:
            raise JSONParseError(f"Failed to parse intent response: {str(e)}")

        if "intent" not in result or "data" not in result:
            raise JSONParseError("Intent response missing required fields")

        result.setdefault("confidence", 0.8)

        if result.get("confidence", 0) < 0.65 and result["intent"] != "chat":
            result = {
                "intent": "chat",
                "confidence": 1.0,
                "data": {"response": "Bạn có thể nói rõ hơn không? Tôi chưa hiểu rõ yêu cầu của bạn."},
            }

        return result

    except (LLMProcessingError, JSONParseError):
        raise
    except Exception as e:
        raise LLMProcessingError(f"Intent parsing failed: {str(e)}")
