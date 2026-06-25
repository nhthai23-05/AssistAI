from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum

_MAX_IMAGE_B64 = 13_500_000  # ~10 MB decoded


class ActionStatusEnum(str, Enum):
    accepted = "accepted"
    rejected = "rejected"


class ActionStatusResponse(BaseModel):
    success: bool


class ActionTypeEnum(str, Enum):
    create_event = "create_event"
    update_event = "update_event"
    delete_event = "delete_event"
    write_sheet = "write_sheet"
    write_income_sheet = "write_income_sheet"
    read_sheet = "read_sheet"
    read_income_sheet = "read_income_sheet"


class SessionStatusEnum(str, Enum):
    active = "active"
    completed = "completed"
    failed = "failed"
    deleted = "deleted"


class ActionLifecycleEnum(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    completed = "completed"
    failed = "failed"


class ChatMessageRequest(BaseModel):
    """Schema for sending a message to the chat"""
    session_id: Optional[int] = Field(None, description="Session ID (created automatically if omitted)")
    message: str = Field("", min_length=0, max_length=10000, description="User message content")
    image_base64: Optional[str] = Field(None, max_length=_MAX_IMAGE_B64, description="Base64-encoded image (JPEG/PNG), max ~10 MB")
    include_context: bool = Field(True, description="Whether to include conversation history for context")

    @model_validator(mode="after")
    def message_or_image_required(self):
        if not self.message.strip() and not self.image_base64:
            raise ValueError("Phải cung cấp message hoặc image_base64")
        return self


class ChatActionData(BaseModel):
    """Data for an action triggered by chat response"""
    action_type: ActionTypeEnum = Field(..., description="Type of action")
    action_status: ActionLifecycleEnum = Field(ActionLifecycleEnum.pending, description="Lifecycle status of the action")
    data: Optional[Any] = Field(None, description="Action-specific data (dict for single item, list for multiple)")
    error: Optional[str] = Field(None, description="Error message if action failed")


class ChatMessageResponse(BaseModel):
    """Schema for chat response"""
    message_id: int = Field(..., description="ID of the response message stored in DB")
    session_id: int
    response: str = Field(..., description="AI response message")
    actions: Optional[List[ChatActionData]] = Field(
        None, 
        description="List of actions triggered by this response"
    )
    tokens_used: int = Field(..., description="Tokens used for this request")
    thinking_time_ms: int = Field(..., description="Time spent generating response (milliseconds)")
    created_at: datetime
    suggested_title: Optional[str] = Field(None, description="AI-generated title for new chat sessions")


class ChatSessionSummary(BaseModel):
    """Summary of a chat session"""
    session_id: int
    title: Optional[str] = None
    message_count: int = Field(..., description="Total messages in session")
    last_message_at: datetime
    total_tokens_used: int
    status: SessionStatusEnum = Field(..., description="Session status")


class ChatHistoryItem(BaseModel):
    """Single item in chat history"""
    message_id: int
    session_id: int
    role: str = Field(..., description="Message role: 'user', 'assistant', 'system'")
    content: str
    created_at: datetime


class ChatSessionDetail(BaseModel):
    """Detailed chat session with history"""
    session_id: int
    user_id: int
    workspace_id: int
    title: Optional[str] = None
    status: SessionStatusEnum
    message_history: List[ChatHistoryItem] = Field(default_factory=list)
    total_messages: int
    total_tokens_used: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
