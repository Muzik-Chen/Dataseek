"""酒店 Pydantic Schema"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HotelOut(BaseModel):
    id: int
    name: str
    region: str
    address: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    stars: int = 3
    price_min: int = 0
    price_max: int = 0
    image_url: str = ""
    tags: Optional[list] = None
    description: str = ""
    is_recommended: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class HotelListParams(BaseModel):
    page: int = 1
    page_size: int = 20
    region: Optional[str] = None
    stars: Optional[int] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    keyword: Optional[str] = None
    is_recommended: Optional[bool] = None
    # 按坐标范围查询
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_km: Optional[float] = None  # 搜索半径，默认 3km
