"""
统一响应格式。
"""
from typing import Any

from pydantic import BaseModel


class APIResponse(BaseModel):
    code: int | str = 0  # 成功时返回 0，错误时返回 "E1xxx" 格式字符串
    message: str = "success"
    data: Any = None


class PaginatedData(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int


def success(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}


def paginated(items: list[Any], total: int, page: int, page_size: int) -> dict:
    return {"code": 0, "message": "success", "data": {"items": items, "total": total, "page": page, "page_size": page_size}}


def error(code: str, message: str, http_status: int = 400) -> dict:
    """返回错误 dict；调用方配合抛出 HTTPException 使用。"""
    return {"code": code, "message": message, "data": None}


# 别名 — 部分 router 使用了 _response 后缀
success_response = success
error_response = error
