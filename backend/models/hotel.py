"""酒店 SQLAlchemy 模型"""
from datetime import datetime

from sqlalchemy import String, DateTime, JSON, Integer, Text, Numeric, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Hotel(Base):
    __tablename__ = "hotels"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(255), default="")
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    stars: Mapped[int] = mapped_column(Integer, default=3)
    price_min: Mapped[int] = mapped_column(Integer, default=0)
    price_max: Mapped[int] = mapped_column(Integer, default=0)
    image_url: Mapped[str] = mapped_column(String(500), default="")
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
