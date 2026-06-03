from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
from config.config import settings
from routers import auth, calendar, chat, sheets
from exceptions import register_exception_handlers

app = FastAPI(title="AssistAI Backend")

# CORS — allow same-origin (served from this server) and common dev ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom exception handlers
register_exception_handlers(app)

# Include routers (must be before static mount)
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(sheets.router, prefix="/api/sheets", tags=["Sheets"])


@app.get("/")
async def root():
    return RedirectResponse(url="/app/AssistAI.html")


@app.get("/health")
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# Serve frontend — mount AFTER all API routes
# Docker: frontend is volume-mounted at /app/frontend (sibling of server.py)
# Local dev: frontend lives one level up at ../../frontend relative to backend/
_here = Path(__file__).parent
_frontend_dir = _here / "frontend" if (_here / "frontend").is_dir() else _here.parent / "frontend"
app.mount("/app", StaticFiles(directory=str(_frontend_dir)), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)