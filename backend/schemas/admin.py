"""
Admin CRUD Pydantic Schemas — 用于 AdminResource 工厂生成的管理后台端点。
"""
from datetime import date, datetime
from pydantic import BaseModel, Field


# ═══ Food ═══

class FoodAdminCreate(BaseModel):
    category_id: int = Field(..., description="分类ID")
    name: str = Field(..., min_length=2, max_length=100)
    type: str = Field("dish", pattern=r"^(dish|shop)$")
    description: str = ""
    image_url: str = ""
    address: str = ""
    price_range: str = ""
    tags: list[str] = []
    is_recommended: bool = False


class FoodAdminUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(None, min_length=2, max_length=100)
    type: str | None = Field(None, pattern=r"^(dish|shop)$")
    description: str | None = None
    image_url: str | None = None
    address: str | None = None
    price_range: str | None = None
    tags: list[str] | None = None
    is_recommended: bool | None = None


class FoodAdminListItem(BaseModel):
    id: int
    category_id: int
    name: str
    type: str
    description: str
    image_url: str
    price_range: str
    tags: list | None = None
    is_recommended: bool
    view_count: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class FoodAdminOut(BaseModel):
    id: int
    category_id: int
    name: str
    type: str
    description: str
    image_url: str
    address: str
    price_range: str
    tags: list | None = None
    is_recommended: bool
    view_count: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ═══ Heritage ═══

class HeritageAdminCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    category: str = Field(..., description="国家级/省级/市级")
    type: str = Field(..., description="传统戏剧/传统技艺/民俗/传统舞蹈/传统美术/传统音乐")
    description: str = ""
    image_url: str = ""
    video_url: str = ""
    inheritor: str = ""
    region: str = Field(..., description="汕头/潮州/揭阳/汕尾")
    address: str = ""


class HeritageAdminUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    category: str | None = None
    type: str | None = None
    description: str | None = None
    image_url: str | None = None
    video_url: str | None = None
    inheritor: str | None = None
    region: str | None = None
    address: str | None = None


class HeritageAdminListItem(BaseModel):
    id: int
    name: str
    category: str
    type: str
    description: str
    image_url: str
    region: str
    view_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class HeritageAdminOut(BaseModel):
    id: int
    name: str
    category: str
    type: str
    description: str
    image_url: str
    video_url: str
    inheritor: str
    region: str
    address: str
    view_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══ FolkEvent ═══

class EventAdminCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = ""
    event_date: date
    lunar_date: str = ""
    region: str = Field(..., description="汕头/潮州/揭阳/汕尾")
    address: str = ""
    image_url: str = ""
    event_type: str = Field(..., pattern=r"^(festival|event|custom)$")


class EventAdminUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = None
    event_date: date | None = None
    lunar_date: str | None = None
    region: str | None = None
    address: str | None = None
    image_url: str | None = None
    event_type: str | None = Field(None, pattern=r"^(festival|event|custom)$")


class EventAdminListItem(BaseModel):
    id: int
    name: str
    description: str
    event_date: date
    lunar_date: str
    region: str
    event_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EventAdminOut(BaseModel):
    id: int
    name: str
    description: str
    event_date: date
    lunar_date: str
    region: str
    address: str
    image_url: str
    event_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══ User ═══

class UserAdminUpdate(BaseModel):
    is_disabled: bool | None = None
    role: str | None = Field(None, pattern=r"^(user|admin)$")
    persona_type: str | None = Field(None, pattern=r"^(tourist|enthusiast|foodie)$")


class UserAdminListItem(BaseModel):
    id: int
    email: str
    nickname: str
    phone: str | None = None
    persona_type: str
    role: str
    is_disabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserAdminOut(BaseModel):
    id: int
    email: str
    nickname: str
    phone: str | None = None
    avatar_url: str
    persona_type: str
    interests: list | None = None
    role: str
    is_disabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══ Settings ═══

class SettingsAdminUpdate(BaseModel):
    # LLM
    llm_provider: str | None = None
    llm_model: str | None = None
    api_key: str | None = None
    # SMTP
    smtp_server: str | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    # 短信 (阿里云)
    sms_access_key: str | None = None
    sms_access_secret: str | None = None
    sms_sign_name: str | None = None
    # 天气
    weather_api_key: str | None = None
