import openai
import json
import re
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config"
PROMPT_PATH = Path(__file__).parent.parent / "prompt"
settings = json.loads((CONFIG_PATH / "settings.json").read_text())

openai.api_key = settings["llm"]["api_key"]

def extract_json(text: str) -> str:
    """
    Extract JSON từ response của GPT (có thể wrapped trong markdown code block)
    """
    # Loại bỏ markdown code block nếu có
    if "```json" in text:
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
    elif "```" in text:
        match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
    
    # Tìm JSON object đầu tiên
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    
    return text

async def chat_completion(message: str, prompt_file: str = None, context: dict = None) -> str:
    """
    Gọi OpenAI API với prompt template từ file
    
    Args:
        message: Tin nhắn từ user
        prompt_file: Tên file prompt trong thư mục prompt/ (ví dụ: "choose_events.txt")
        context: Dictionary chứa biến để thay thế trong prompt template
    
    Returns:
        Response từ OpenAI API
    """
    try:
        # Nếu có prompt file, đọc và format với context
        if prompt_file:
            prompt_path = PROMPT_PATH / prompt_file
            if prompt_path.exists():
                prompt_template = prompt_path.read_text(encoding='utf-8')
                
                # Thay thế biến trong template nếu có context
                if context:
                    for key, value in context.items():
                        prompt_template = prompt_template.replace(f"{{{key}}}", str(value))
                
                # Kết hợp prompt template với message
                full_message = f"{prompt_template}\n\nUser input: {message}"
            else:
                full_message = message
        else:
            full_message = message
        
        # DEBUG: In ra prompt info
        print("="*80)
        print("DEBUG - Full Prompt Length:", len(full_message))
        print("DEBUG - First 500 chars:")
        print(full_message[:500])
        print("="*80)
        
        # Sử dụng OpenAI API mới (>= 1.0)
        from openai import OpenAI
        client = OpenAI(api_key=openai.api_key)
        
        print("DEBUG - Calling OpenAI API...")
        print(f"DEBUG - Model: {settings['llm']['model']}")
        
        response = client.chat.completions.create(
            model=settings["llm"]["model"],
            messages=[{"role": "user", "content": full_message}],
            max_completion_tokens=settings["llm"].get("max_completion_tokens", 1000)
        )
        
        result = response.choices[0].message.content
        
        print(f"DEBUG - Response received, length: {len(result) if result else 0}")
        
        if not result or result.strip() == "":
            raise ValueError("OpenAI returned empty response")
        
        return result
        
    except Exception as e:
        error_msg = f"OpenAI API Error: {str(e)}"
        print(f"❌ {error_msg}")
        
        # In thêm thông tin debug
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        
        raise Exception(error_msg)

async def smart_event_operation(user_request: str, events_list: list, operation: str = "update") -> dict:
    try:
        # Format events list thành text dễ đọc
        events_text = "\n".join([
            f"ID: {event.get('id')}\n"
            f"Tên: {event.get('summary')}\n"
            f"Bắt đầu: {event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))}\n"
            f"Kết thúc: {event.get('end', {}).get('dateTime', event.get('end', {}).get('date'))}\n"
            f"Địa điểm: {event.get('location', 'N/A')}\n"
            for event in events_list
        ])
        
        context = {
            "events": events_text,
            "request": user_request
        }
        
        # Chọn prompt file tương ứng
        prompt_file = "choose_events.txt" if operation == "update" else "delete_event.txt"
        
        response = await chat_completion(
            message=user_request,
            prompt_file=prompt_file,
            context=context
        )
        
        # DEBUG: In ra response từ Chatgpt
        print("="*80)
        print(f"DEBUG - GPT Response ({operation}):")
        print(response)
        print("="*80)
        
        json_str = extract_json(response)       
        result = json.loads(json_str)
        return result
        
    except Exception as e:
        print(f"Lỗi khi thực hiện {operation} event: {e}")
        print(f"Response was: {response if 'response' in locals() else 'No response'}")
        raise

async def parse_event_creation(user_request: str, current_date: str = None, events_list: list = None) -> dict:
    """
    Sử dụng GPT để phân tích yêu cầu tạo event và chuyển thành cấu trúc dữ liệu
    
    Args:
        user_request: Yêu cầu của user (ví dụ: "tạo meeting với team vào 3pm mai")
        current_date: Ngày hiện tại để GPT có context thời gian
        events_list: Danh sách events hiện tại để tránh xung đột
    
    Returns:
        Dict chứa thông tin event cần tạo
    """
    try:
        from datetime import datetime
        
        if not current_date:
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format events list nếu có
        if events_list:
            events_text = "\n".join([
                f"- {event.get('summary', 'No title')}: "
                f"{event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'N/A'))} → "
                f"{event.get('end', {}).get('dateTime', event.get('end', {}).get('date', 'N/A'))}"
                for event in events_list
            ])
        else:
            events_text = "Không có events nào trong tuần này"
        
        context = {
            "request": user_request,
            "current_date": current_date,
            "events": events_text
        }
        
        response = await chat_completion(
            message=user_request,
            prompt_file="create_event.txt",
            context=context
        )
        
        # DEBUG: In ra response để xem
        print("="*80)
        print("DEBUG - GPT Response:")
        print(response)
        print("="*80)
        
        # Extract và parse JSON response từ GPT
        json_str = extract_json(response)
        print("DEBUG - Extracted JSON:")
        print(json_str)
        print("="*80)
        
        result = json.loads(json_str)
        return result
        
    except Exception as e:
        print(f"Lỗi khi phân tích event creation: {e}")
        print(f"Response was: {response if 'response' in locals() else 'No response'}")
        raise

async def detect_calendar_action(user_request: str) -> dict:
    """
    Sử dụng LLM để phát hiện action từ user request
    
    Args:
        user_request: Yêu cầu của user
    
    Returns:
        Dict chứa action, confidence, reasoning
    """
    try:
        context = {
            "request": user_request
        }
        
        response = await chat_completion(
            message=user_request,
            prompt_file="detect_action.txt",
            context=context
        )
        
        # Extract và parse JSON
        json_str = extract_json(response)
        result = json.loads(json_str)
        
        return result
        
    except Exception as e:
        print(f"Lỗi khi detect action: {e}")
        # Fallback về create nếu có lỗi
        return {"action": "create", "confidence": 0.5, "reasoning": "Error - defaulting to create"}
