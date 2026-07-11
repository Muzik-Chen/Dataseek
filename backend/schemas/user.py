"""用户模块 Schema — 个人中心/收藏/偏好。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- 用户信息 ---
class UserOut(BaseModel):
    id: int
    email: str
    phone: Optional[str] = None
    nickname: str = ""
    avatar_url: str = ""
    persona_type: str = "tourist"
    interests: Optional[list[str]] = None
    role: str = "user"
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = Field(None, min_length=2, max_length=20)
    avatar_url: Optional[str] = None
    persona_type: Optional[str] = None
    interests: Optional[list[str]] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)


# --- 收藏 ---
class FavoriteOut(BaseModel):
    id: int
    user_id: int
    item_type: str
    item_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FavoriteCreate(BaseModel):
    item_type: str = Field(pattern=r"^(food|heritage|event)$")
    item_id: int


class FavoriteListParams(BaseModel):
    page: int = 1
    page_size: int = 20
    item_type: Optional[str] = None
