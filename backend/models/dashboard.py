from datetime import datetime

from sqlalchemy import String, DateTime, Integer, DECIMAL, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class WeatherRecord(Base):
    __tablename__ = "weather_records"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    temperature: Mapped[float] = mapped_column(DECIMAL(5, 1), nullable=False)
    humidity: Mapped[int] = mapped_column(Integer, nullable=False)
    weather_desc: Mapped[str] = mapped_column(String(50), nullable=False)
    wind_level: Mapped[int] = mapped_column(Integer, default=0)
    record_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CrowdRecord(Base):
    __tablename__ = "crowd_records"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    location_name: Mapped[str] = mapped_column(String(100), nullable=False)
    crowd_level: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_count: Mapped[int] = mapped_column(Integer, default=0)
    record_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CrowdLocation(Base):
    """人流监测点经纬度字典表 — 存储各监测点的固定坐标信息。"""
    __tablename__ = "crowd_locations"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location_name: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    base_capacity: Mapped[int] = mapped_column(Integer, default=1000)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
