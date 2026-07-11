"""行程规划模块 Schema。"""
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


class TripPlanCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    days: int = Field(ge=1, le=30)
    crowd_type: str = Field(default="solo")  # solo/couple/family/friends
    preferences: list[str] = []  # ["美食", "非遗", "自然风光"]
    origin: str = Field(default="广州")  # 出发城市
    budget: str = Field(default="mid")  # low/mid/high


class TripPlanOut(BaseModel):
    id: int
    user_id: int
    title: str
    days: int
    crowd_type: str
    preferences: Any = {}  # list or dict — JSON column stores both
    plan_content: Optional[dict] = None
    status: str = "generated"
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TripPlanImport(BaseModel):
    """导入已生成的行程计划（含富化数据），不调用 AI。"""
    title: str = Field(min_length=1, max_length=100)
    days: int = Field(ge=1, le=30)
    crowd_type: str = Field(default="solo")
    preferences: list[str] = []
    plan_content: dict  # 完整 plan JSON（含 enrichment + route_geo）


class TripPlanStreamRequest(BaseModel):
    """SSE 流式行程生成请求 — 无需 title，直接传递参数给 AI。"""
    origin: str = Field(default="广州")
    days: int = Field(ge=1, le=30, default=3)
    crowd_type: str = Field(default="solo")  # solo/couple/family/friends
    preferences: list[str] = []  # ["美食", "非遗", "自然风光"]
    budget: str = Field(default="mid")  # low/mid/high


class TripPlanListParams(BaseModel):
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None


class TripPlanRefineRequest(BaseModel):
    """行程方案调整请求 — 用户对已生成方案提出修改意见。"""
    plan: dict  # 原始 plan 对象（含 plan_id/enrichment/route_geo）
    request: str = Field(min_length=1, max_length=500)  # 用户修改要求


class TripPlanDraftCreate(BaseModel):
    """AI 生成完成时自动保存 — 含完整方案内容。"""
    title: str = Field(min_length=1, max_length=100)
    days: int = Field(ge=1, le=30)
    crowd_type: str = Field(default="solo")
    preferences: list[str] = []
    plan_content: dict  # 完整方案内容（与 importPlan 相同）


class TripPlanUpdate(BaseModel):
    """更新已有行程（草稿升级为正式方案等）。"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    plan_content: Optional[dict] = None
    status: Optional[str] = None
