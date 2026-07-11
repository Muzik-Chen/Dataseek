from datetime import datetime, date

from sqlalchemy import String, DateTime, JSON, Integer, Text, Date, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Heritage(Base):
    __tablename__ = "heritages"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)   # 国家级/省级/市级
    type: Mapped[str] = mapped_column(String(50), nullable=False)       # 传统戏剧/传统技艺/民俗...
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    video_url: Mapped[str] = mapped_column(String(500), default="")
    inheritor: Mapped[str] = mapped_column(String(50), default="")
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    address: Mapped[str] = mapped_column(String(255), default="")
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FolkEvent(Base):
    __tablename__ = "folk_events"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    lunar_date: Mapped[str] = mapped_column(String(50), default="")
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    address: Mapped[str] = mapped_column(String(255), default="")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    event_type: Mapped[str] = mapped_column(String(10), nullable=False)  # festival/event/custom
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
