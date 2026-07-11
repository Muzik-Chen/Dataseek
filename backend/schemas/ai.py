"""统一 AI 聊天接口 Schema。"""
from typing import Optional
from pydantic import BaseModel, Field


class ChatAIRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = None
