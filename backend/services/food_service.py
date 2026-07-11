"""
美食业务逻辑 — 列表筛选/详情/分类/AI推荐。
"""
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from models.food import Food, FoodCategory


async def list_foods(
    db: AsyncSession,
    page: int = 1, page_size: int = 20,
    category_id: int | None = None,
    food_type: str | None = None,
    keyword: str | None = None,
    sort: str = "view_count",
    price_range: str | None = None,
    is_recommended: bool | None = None,
) -> tuple[list[Food], int]:
    """美食列表（分页+筛选+搜索+排序）。"""
    q = select(Food)
    count_q = select(func.count(Food.id))

    if category_id:
        q = q.where(Food.category_id == category_id)
        count_q = count_q.where(Food.category_id == category_id)
    if food_type:
        q = q.where(Food.type == food_type)
        count_q = count_q.where(Food.type == food_type)
    if price_range:
        q = q.where(Food.price_range == price_range)
        count_q = count_q.where(Food.price_range == price_range)
    if is_recommended is not None:
        q = q.where(Food.is_recommended == is_recommended)
        count_q = count_q.where(Food.is_recommended == is_recommended)
    if keyword:
        q = q.where(Food.name.contains(keyword))
        count_q = count_q.where(Food.name.contains(keyword))

    # 排序
    sort_col = desc(Food.view_count)  # 默认
    if sort == "created_at":
        sort_col = desc(Food.created_at)
    elif sort == "price_range":
        sort_col = asc(Food.price_range)
    q = q.order_by(sort_col)

    total = (await db.execute(count_q)).scalar()
    offset = (page - 1) * page_size
    rows = (await db.execute(q.offset(offset).limit(page_size))).scalars().all()

    return list(rows), total


async def get_food_detail(db: AsyncSession, food_id: int) -> Food:
    """获取美食详情，自动 +1 浏览量。"""
    food = (await db.execute(
        select(Food).where(Food.id == food_id)
    )).scalar()
    if not food:
        raise ValueError("美食不存在")
    food.view_count = (food.view_count or 0) + 1
    await db.flush()
    return food


async def list_categories(db: AsyncSession) -> list[FoodCategory]:
    """获取所有美食分类（按 sort_order 排序）。"""
    rows = (await db.execute(
        select(FoodCategory).order_by(FoodCategory.sort_order)
    )).scalars().all()
    return list(rows)


async def get_hot_foods(db: AsyncSession, limit: int = 50) -> list[dict]:
    """获取热门美食候选池（供 AI 推荐使用）。"""
    rows = (await db.execute(
        select(Food)
        .where(Food.is_recommended == True)
        .order_by(desc(Food.view_count))
        .limit(limit)
    )).scalars().all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "category_id": f.category_id,
            "type": f.type,
            "description": f.description,
            "tags": f.tags,
            "price_range": f.price_range,
            "address": f.address,
        }
        for f in rows
    ]
