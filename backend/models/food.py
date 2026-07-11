from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, DECIMAL, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class FoodCategory(Base):
    __tablename__ = "food_categories"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    icon: Mapped[str] = mapped_column(String(255), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Food(Base):
    __tablename__ = "foods"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False, default="dish")  # dish | shop
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    address: Mapped[str] = mapped_column(String(255), default="")
    latitude: Mapped[float | None] = mapped_column(DECIMAL(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(DECIMAL(10, 7), nullable=True)
    price_range: Mapped[str] = mapped_column(String(20), default="")
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float | None] = mapped_column(DECIMAL(2, 1), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
