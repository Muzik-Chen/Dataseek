from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FoodOut(BaseModel):
    id: int
    category_id: int
    category_name: Optional[str] = ""
    name: str
    type: str
    description: str = ""
    image_url: str = ""
    address: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price_range: Optional[str] = None
    tags: Optional[list[str]] = None
    is_recommended: bool = False
    view_count: int = 0
    rating: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FoodListParams(BaseModel):
    page: int = 1
    page_size: int = 20
    category_id: Optional[int] = None
    type: Optional[str] = None
    keyword: Optional[str] = None
    sort: Optional[str] = "view_count"
    is_recommended: Optional[bool] = None


class CategoryOut(BaseModel):
    id: int
    name: str
    icon: str = ""
    sort_order: int = 0

    model_config = {"from_attributes": True}


class RecommendRequest(BaseModel):
    preference: str


class RecommendItem(BaseModel):
    food_id: int
    name: str
    reason: str
    score: float


class RecommendOut(BaseModel):
    recommendations: list[RecommendItem]
    summary: str
