"""数据大屏模块 Schema — 天气 + 人流。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WeatherOut(BaseModel):
    id: int
    region: str
    temperature: float
    humidity: int
    weather_desc: str
    wind_level: int = 0
    record_time: datetime
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WeatherQuery(BaseModel):
    region: Optional[str] = None
    limit: int = 24  # 最近 N 条记录


class CrowdOut(BaseModel):
    id: int
    region: str
    location_name: str
    crowd_level: int
    estimated_count: int = 0
    record_time: datetime
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CrowdGeoOut(BaseModel):
    """带经纬度的人流数据（供地图使用）。"""
    id: int
    region: str
    location_name: str
    latitude: float
    longitude: float
    crowd_level: int
    estimated_count: int = 0
    base_capacity: int = 1000
    record_time: datetime

    model_config = {"from_attributes": True}


class CrowdQuery(BaseModel):
    region: Optional[str] = None
    limit: int = 24


class WeatherGeoOut(BaseModel):
    """按坐标查询的天气结果（返回最近城市天气）。"""
    region: str
    city: str
    temperature: float
    humidity: int
    weather_desc: str
    wind_level: int = 0
    distance_km: float = 0.0
    record_time: Optional[datetime] = None


class WeatherRouteOut(BaseModel):
    """路线天气摘要。"""
    waypoints: list[dict] = []  # [{lat, lng, city, weather}]
    summary: str = ""


class DashboardOverview(BaseModel):
    """数据大屏概览"""
    total_users: int = 0
    total_foods: int = 0
    total_heritages: int = 0
    total_posts: int = 0
    today_chats: int = 0
    active_users_today: int = 0
    hot_regions: list[dict] = []  # [{region, crowd_level, temperature}]
