"""
ChatSession ORM 模型 — 会话状态持久化。
"""
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Text, func, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(200), default="新对话")
    intent_state: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="intent/collected_params/turn/interest_hints")
    status: Mapped[str] = mapped_column(String(10), default="active", comment="active / closed")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
