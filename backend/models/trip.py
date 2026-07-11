from datetime import datetime

from sqlalchemy import String, DateTime, JSON, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class TripPlan(Base):
    __tablename__ = "trip_plans"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    crowd_type: Mapped[str] = mapped_column(String(20), nullable=False)
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False)
    plan_content: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="generated")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
