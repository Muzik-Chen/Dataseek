"""
美食模块路由 — 列表/详情/分类/AI推荐。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db
from models.food import Food, FoodCategory
from schemas.food import (
    FoodOut, FoodListParams, CategoryOut,
    RecommendRequest, RecommendOut, RecommendItem,
)
from utils.response import success, paginated

router = APIRouter(prefix="/foods", tags=["美食"])


@router.get("")
async def list_foods(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: int | None = None,
    type: str | None = None,
    keyword: str | None = None,
    sort: str = "view_count",
    is_recommended: bool | None = None,
    price_range: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Food)
    count_q = select(func.count(Food.id))

    if category_id:
        q = q.where(Food.category_id == category_id)
        count_q = count_q.where(Food.category_id == category_id)
    if type:
        q = q.where(Food.type == type)
        count_q = count_q.where(Food.type == type)
    if keyword:
        q = q.where(Food.name.contains(keyword))
        count_q = count_q.where(Food.name.contains(keyword))
    if is_recommended is not None:
        q = q.where(Food.is_recommended == is_recommended)
        count_q = count_q.where(Food.is_recommended == is_recommended)
    if price_range:
        q = q.where(Food.price_range == price_range)
        count_q = count_q.where(Food.price_range == price_range)

    # 排序
    sort_map = {
        "view_count": Food.view_count.desc(),
        "created_at": Food.created_at.desc(),
        "price_range": Food.price_range.asc(),
    }
    order = sort_map.get(sort, Food.view_count.desc())
    q = q.order_by(order)

    # 分页
    offset = (page - 1) * page_size
    q = q.offset(offset).limit(page_size)

    total = (await db.execute(count_q)).scalar()
    rows = (await db.execute(q)).scalars().all()

    # 关联分类名称
    cat_ids = {r.category_id for r in rows}
    cat_map = {}
    if cat_ids:
        cats = (await db.execute(
            select(FoodCategory).where(FoodCategory.id.in_(cat_ids))
        )).scalars().all()
        cat_map = {c.id: c.name for c in cats}

    items = []
    for r in rows:
        d = FoodOut.model_validate(r).model_dump()
        d["category_name"] = cat_map.get(r.category_id, "")
        items.append(d)

    return paginated(items, total, page, page_size)


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    q = select(FoodCategory).order_by(FoodCategory.sort_order)
    rows = (await db.execute(q)).scalars().all()
    return success([CategoryOut.model_validate(r).model_dump() for r in rows])


@router.get("/{food_id}")
async def get_food(food_id: int, db: AsyncSession = Depends(get_db)):
    food = (await db.execute(select(Food).where(Food.id == food_id))).scalar()
    if not food:
        raise HTTPException(status_code=404, detail="美食不存在")
    # 自动 +1 view_count
    food.view_count += 1
    await db.flush()

    d = FoodOut.model_validate(food).model_dump()
    cat = (await db.execute(select(FoodCategory).where(FoodCategory.id == food.category_id))).scalar()
    d["category_name"] = cat.name if cat else ""
    return success(d)


@router.post("/recommend")
async def recommend_foods(req: RecommendRequest, db: AsyncSession = Depends(get_db)):
    """
    AI 美食推荐 — 占位实现（返回热门推荐作为兜底）。
    后续接入 LangChain LLM 后替换为真实 AI 推荐。
    """
    if not req.preference or len(req.preference.strip()) < 2:
        raise HTTPException(status_code=400, detail="请至少输入2个字描述您的偏好")

    # 从数据库取热门美食作为候选
    q = select(Food).where(Food.is_recommended == True).order_by(Food.view_count.desc()).limit(6)
    rows = (await db.execute(q)).scalars().all()

    if not rows:
        q = select(Food).order_by(Food.view_count.desc()).limit(6)
        rows = (await db.execute(q)).scalars().all()

    cat_ids = {r.category_id for r in rows}
    cats = (await db.execute(select(FoodCategory).where(FoodCategory.id.in_(cat_ids)))).scalars().all()
    cat_map = {c.id: c.name for c in cats}

    recommendations = []
    for r in rows[:4]:
        recommendations.append(RecommendItem(
            food_id=r.id,
            name=r.name,
            reason=f"热门推荐 — {cat_map.get(r.category_id, '')}",
            score=0.85,
        ))

    return success(RecommendOut(
        recommendations=recommendations,
        summary=f"[{req.preference}] 为您找到 {len(recommendations)} 个推荐结果",
    ).model_dump())
