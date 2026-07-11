from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel


class HeritageOut(BaseModel):
    id: int
    name: str
    category: str
    type: str
    description: str = ""
    image_url: str = ""
    video_url: str = ""
    inheritor: str = ""
    region: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: str = ""
    view_count: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class HeritageListParams(BaseModel):
    page: int = 1
    page_size: int = 20
    category: Optional[str] = None
    type: Optional[str] = None
    region: Optional[str] = None
    keyword: Optional[str] = None
    is_recommended: Optional[bool] = None


class FolkEventOut(BaseModel):
    id: int
    name: str
    description: str = ""
    event_date: date
    lunar_date: str = ""
    region: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: str = ""
    image_url: str = ""
    event_type: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FolkEventListParams(BaseModel):
    page: int = 1
    page_size: int = 20
    event_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    region: Optional[str] = None


class FolkEventCreate(BaseModel):
    name: str
    description: str = ""
    event_date: date
    lunar_date: str = ""
    region: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: str = ""
    image_url: str = ""
    event_type: str


class FolkEventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[date] = None
    lunar_date: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    image_url: Optional[str] = None
    event_type: Optional[str] = None
