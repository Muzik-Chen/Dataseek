"""私信模块 Schema。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MessageSend(BaseModel):
    receiver_id: int
    content: str = Field(min_length=1, max_length=5000)


class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    user_id: int
    user_nickname: str = ""
    user_avatar: str = ""
    last_message: str = ""
    unread_count: int = 0
    updated_at: Optional[datetime] = None


class MessageListParams(BaseModel):
    page: int = 1
    page_size: int = 20
    before_id: Optional[int] = None  # 加载更早消息
