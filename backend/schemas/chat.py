"""智能客服模块 Schema。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatMessageOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    session_id: str
    role: str
    content: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ChatSendRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = None  # 新会话可不传


class ChatSendOut(BaseModel):
    session_id: str
    reply: str
    sources: list[dict] = []  # RAG 引用来源


class ChatSessionOut(BaseModel):
    session_id: str
    title: str
    last_message: str = ""
    message_count: int = 0
    updated_at: Optional[datetime] = None


class ChatHistoryParams(BaseModel):
    page: int = 1
    page_size: int = 20
