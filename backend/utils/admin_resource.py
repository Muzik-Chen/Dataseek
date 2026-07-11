"""
AdminResource — Django-Admin 风格的通用 CRUD 工厂。

用法:
    from models.food import Food
    from schemas.admin import FoodAdminCreate, FoodAdminUpdate, FoodAdminOut, FoodAdminListItem

    food_admin = AdminResource(
        model=Food,
        schemas={
            "create": FoodAdminCreate,
            "update": FoodAdminUpdate,
            "out": FoodAdminOut,
            "list_item": FoodAdminListItem,
        },
        config={
            "prefix": "/foods",
            "list_display": ["id", "name", "category_id", "type", "is_recommended"],
            "search_fields": ["name", "description"],
            "filter_fields": ["category_id", "type", "is_recommended"],
            "enabled_actions": ["list", "detail", "create", "update", "delete"],
        },
    )
    router = food_admin.get_router()
    app.include_router(router, prefix="/api/v1/admin")
"""
from typing import Any, Callable

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from utils.dependencies import require_admin
from utils.response import success, paginated, error


class AdminResource:
    """为 SQLAlchemy Model 自动生成 5 个标准管理后台 CRUD 端点。"""

    def __init__(
        self,
        *,
        model: type,
        schemas: dict[str, type],
        config: dict[str, Any],
        hooks: dict[str, Callable] | None = None,
    ):
        """
        Args:
            model: SQLAlchemy 模型类
            schemas: {"create", "update", "out", "list_item"} 的 Pydantic schema
            config:
                - prefix: URL 前缀，如 "/foods"
                - list_display: 返回字段列表（列表接口用）
                - search_fields: 搜索字段列表（LIKE 查询）
                - filter_fields: 筛选字段列表（精确匹配 query params）
                - enabled_actions: 启用的端点，默认全部 ["list","detail","create","update","delete"]
            hooks: 可选钩子函数
                {before_create, after_create, before_update, after_update,
                 before_delete, after_delete} → async Callable(db, data)
        """
        self.model = model
        self.schemas = schemas
        self.config = config
        self.hooks = hooks or {}
        self.prefix = config["prefix"]
        self.enabled = config.get("enabled_actions", ["list", "detail", "create", "update", "delete"])
        self.search_fields = config.get("search_fields", [])
        self.filter_fields = config.get("filter_fields", [])
        self._router = None

    # ── helpers ──────────────────────────────────────────────

    def _pk_name(self) -> str:
        """返回主键列名，默认 "id"。"""
        return "id"

    async def _run_hook(self, name: str, db: AsyncSession, data: Any = None):
        hook = self.hooks.get(name)
        if hook:
            await hook(db, data)

    def _apply_search(self, query, keyword: str):
        """LIKE 搜索 — 对 search_fields 中每个字段做 OR 查询。"""
        if not keyword or not self.search_fields:
            return query
        conditions = []
        for field_name in self.search_fields:
            col = getattr(self.model, field_name, None)
            if col is not None:
                conditions.append(col.contains(keyword))
        if conditions:
            # OR 串联所有条件
            from sqlalchemy import or_
            query = query.where(or_(*conditions))
        return query

    def _apply_filters(self, query, params: dict):
        """精确筛选 — 对 filter_fields 中每个字段做 == 匹配。"""
        for field_name in self.filter_fields:
            value = params.get(field_name)
            if value is None:
                continue
            col = getattr(self.model, field_name, None)
            if col is not None:
                query = query.where(col == value)
        return query

    # ── endpoints ────────────────────────────────────────────

    async def _list(self, db: AsyncSession, page: int, page_size: int,
                    keyword: str, **filters):
        """GET {prefix} — 分页列表。"""
        query = select(self.model)
        query = self._apply_search(query, keyword)
        query = self._apply_filters(query, filters)

        # count
        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar()

        # fetch
        rows = (await db.execute(
            query.order_by(self.model.created_at.desc())
                 .offset((page - 1) * page_size)
                 .limit(page_size)
        )).scalars().all()

        return paginated(
            items=[self.schemas["list_item"].model_validate(r).model_dump() for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def _detail(self, pk: int, db: AsyncSession):
        """GET {prefix}/{id} — 单条详情。"""
        row = await db.get(self.model, pk)
        if not row:
            raise HTTPException(404, detail="资源不存在")
        return success(self.schemas["out"].model_validate(row).model_dump())

    async def _create(self, body, db: AsyncSession):
        """POST {prefix} — 创建。"""
        await self._run_hook("before_create", db, body)
        obj = self.model(**body.model_dump())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        await self._run_hook("after_create", db, obj)
        return success(
            self.schemas["out"].model_validate(obj).model_dump(),
            message="创建成功",
        )

    async def _update(self, pk: int, body, db: AsyncSession):
        """PUT {prefix}/{id} — 更新。"""
        row = await db.get(self.model, pk)
        if not row:
            raise HTTPException(404, detail="资源不存在")

        await self._run_hook("before_update", db, {"row": row, "data": body})

        # 只更新非 None 字段
        update_data = body.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(row, key, value)

        await db.commit()
        await db.refresh(row)
        await self._run_hook("after_update", db, row)
        return success(
            self.schemas["out"].model_validate(row).model_dump(),
            message="更新成功",
        )

    async def _delete(self, pk: int, db: AsyncSession):
        """DELETE {prefix}/{id} — 删除。"""
        row = await db.get(self.model, pk)
        if not row:
            raise HTTPException(404, detail="资源不存在")

        await self._run_hook("before_delete", db, row)
        await db.delete(row)
        await db.commit()
        await self._run_hook("after_delete", db, row)
        return success(message="删除成功")

    # ── router factory ───────────────────────────────────────

    def get_router(self) -> APIRouter:
        """生成 APIRouter，包含所有启用的端点。"""
        if self._router:
            return self._router

        router = APIRouter(prefix=self.prefix, tags=[f"管理后台{self.prefix}"])

        # 构造动态路径函数 — 必须在工厂方法内部定义以闭合 self
        pk = self._pk_name()

        if "list" in self.enabled:
            async def _list_endpoint(
                request: Request,
                page: int = Query(1, ge=1),
                page_size: int = Query(20, ge=1, le=100),
                keyword: str = Query(""),
                db: AsyncSession = Depends(get_db),
                _admin=Depends(require_admin),
            ):
                # 从 query params 提取 filter_fields
                filters = {}
                for f in self.filter_fields:
                    val = request.query_params.get(f)
                    if val is not None:
                        # 尝试转换 bool
                        if val.lower() in ("true", "false"):
                            filters[f] = val.lower() == "true"
                        elif val.isdigit():
                            filters[f] = int(val)
                        else:
                            filters[f] = val
                return await self._list(db, page, page_size, keyword, **filters)

            router.get("")(_list_endpoint)

        if "detail" in self.enabled:
            async def _detail_endpoint(
                id: int,
                db: AsyncSession = Depends(get_db),
                _admin=Depends(require_admin),
            ):
                return await self._detail(id, db)

            router.get(f"/{{{pk}}}")(_detail_endpoint)

        if "create" in self.enabled:
            schema_create = self.schemas.get("create")
            if schema_create:

                async def _create_endpoint(
                    body: schema_create,
                    db: AsyncSession = Depends(get_db),
                    _admin=Depends(require_admin),
                ):
                    return await self._create(body, db)

                router.post("")(_create_endpoint)

        if "update" in self.enabled:
            schema_update = self.schemas.get("update")
            if schema_update:

                async def _update_endpoint(
                    id: int,
                    body: schema_update,
                    db: AsyncSession = Depends(get_db),
                    _admin=Depends(require_admin),
                ):
                    return await self._update(id, body, db)

                router.put(f"/{{{pk}}}")(_update_endpoint)

        if "delete" in self.enabled:
            async def _delete_endpoint(
                id: int,
                db: AsyncSession = Depends(get_db),
                _admin=Depends(require_admin),
            ):
                return await self._delete(id, db)

            router.delete(f"/{{{pk}}}")(_delete_endpoint)

        self._router = router
        return router
