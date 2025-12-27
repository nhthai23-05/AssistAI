import openai
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config"
settings = json.loads((CONFIG_PATH / "settings.json").read_text())

openai.api_key = settings["llm"]["api_key"]

async def chat_completion(message: str) -> str:
    """Gọi OpenAI API"""
    try:
        response = openai.ChatCompletion.create(
            model=settings["llm"]["model"],
            messages=[{"role": "user", "content": message}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"