"""社区推荐模块 Schema。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- 动态 ---
class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)
    images: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    post_type: str = Field(default="recommend")  # recommend/challenge/social/study


class PostOut(BaseModel):
    id: int
    user_id: int
    user_nickname: Optional[str] = ""
    user_avatar: Optional[str] = ""
    title: str
    content: str
    images: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    post_type: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    is_liked: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PostListParams(BaseModel):
    page: int = 1
    page_size: int = 20
    post_type: Optional[str] = None
    tag: Optional[str] = None
    keyword: Optional[str] = None
    sort: Optional[str] = "created_at"  # created_at | like_count | comment_count


# --- 评论 ---
class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    parent_id: Optional[int] = None


class CommentOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    user_nickname: Optional[str] = ""
    user_avatar: Optional[str] = ""
    content: str
    parent_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CommentListParams(BaseModel):
    page: int = 1
    page_size: int = 20
