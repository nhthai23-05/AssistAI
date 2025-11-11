from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
from services.calendar_service import list_events
from services.ai_service import chat_completion

app = FastAPI(title="AssistAI Backend")

# CORS cho Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config
CONFIG_PATH = Path(__file__).parent / "config"
settings = json.loads((CONFIG_PATH / "settings.json").read_text())

@app.get("/")
async def root():
    return {"message": "AssistAI Backend Running"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/api/calendar/events")
async def get_events(max_results: int = 10):
    events = await list_events(max_results)
    return {"events": events}

@app.post("/api/chat")
async def chat(request: dict):
    message = request.get("message", "")
    reply = await chat_completion(message)
    return {"reply": reply}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)