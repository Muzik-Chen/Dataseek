"""
行程规划路由 — 创建/查看/删除行程，AI 生成行程内容。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.trip import TripPlan
from models.user import User
from schemas.trip import TripPlanCreate, TripPlanOut, TripPlanImport, TripPlanStreamRequest, TripPlanRefineRequest, TripPlanListParams, TripPlanDraftCreate, TripPlanUpdate
from utils.response import success, paginated
from utils.dependencies import get_current_user
from ai.prompts import sse_event

router = APIRouter(prefix="/trip", tags=["行程规划"])


@router.post("/plan")
async def create_trip_plan(
    req: TripPlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建行程计划并调用 AI 生成行程内容。"""
    # 创建行程记录
    plan = TripPlan(
        user_id=current_user.id,
        title=req.title,
        days=req.days,
        crowd_type=req.crowd_type,
        preferences=req.preferences,
        status="generating",
    )
    db.add(plan)
    await db.flush()

    # --- AI 行程生成 ---
    try:
        from ai.trip_agent import generate_three_plans
        print(f"[Trip] Generating plans for: origin={req.origin}, days={req.days}, "
              f"crowd={req.crowd_type}, interests={req.preferences}, budget={req.budget}")
        plans = await generate_three_plans({
            "origin": req.origin,
            "days": req.days,
            "crowd_type": req.crowd_type,
            "interests": req.preferences if req.preferences else [],
            "budget": req.budget,
        })
        print(f"[Trip] Generated {len(plans)} plans")
        plan.plan_content = {"plans": plans, "crowd_type": req.crowd_type, "origin": req.origin}
        plan.status = "generated"
    except Exception as e:
        import traceback
        print(f"[Trip] AI generation failed, falling back to template: {e}")
        traceback.print_exc()
        plan.plan_content = _generate_plan(req.days, req.preferences, req.crowd_type)
        plan.status = "generated"
    await db.flush()
    await db.refresh(plan)

    return success(TripPlanOut.model_validate(plan).model_dump())


@router.post("/plan/stream")
async def create_trip_plan_stream(
    req: TripPlanStreamRequest,
    current_user: User = Depends(get_current_user),
):
    """SSE 流式生成行程方案 — 渐进式返回 AI 规划过程与结果。

    前端通过 EventSource/fetch+reader 消费 SSE 事件流：
      thinking → token → trip_card × N → route_* → done
    """
    from ai.trip_agent import generate_trip_plans_stream

    async def event_generator():
        try:
            async for event_str in generate_trip_plans_stream({
                "origin": req.origin,
                "days": req.days,
                "crowd_type": req.crowd_type,
                "interests": req.preferences if req.preferences else [],
                "budget": req.budget,
            }):
                yield event_str
        except Exception as e:
            import traceback
            print(f"[Trip] SSE stream error: {e}")
            traceback.print_exc()
            yield sse_event("error", message=f"行程规划失败: {str(e)}")
        yield sse_event("done")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/plan/refine")
async def refine_trip_plan(
    req: TripPlanRefineRequest,
    current_user: User = Depends(get_current_user),
):
    """SSE 流式调整行程方案 — 用户对已生成方案提出修改意见。

    前端通过 fetch+reader 消费 SSE 事件流：
      thinking → token → trip_card → route_* → done
    """
    from ai.refine_agent import refine_plan_stream

    async def event_generator():
        try:
            async for event_str in refine_plan_stream(req.plan, req.request):
                yield event_str
        except Exception as e:
            import traceback
            print(f"[Trip] Refine stream error: {e}")
            traceback.print_exc()
            yield sse_event("error", message=f"方案调整失败: {str(e)}")
        yield sse_event("done")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/plan/import")
async def import_trip_plan(
    req: TripPlanImport,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """导入已生成的行程计划（含富化数据），不再调用 AI。"""
    plan = TripPlan(
        user_id=current_user.id,
        title=req.title,
        days=req.days,
        crowd_type=req.crowd_type,
        preferences=req.preferences,
        plan_content=req.plan_content,
        status="generated",
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return success(TripPlanOut.model_validate(plan).model_dump())


@router.post("/plan/draft")
async def create_trip_draft(
    req: TripPlanDraftCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 生成完成时自动保存草稿（含完整方案内容）。"""
    plan = TripPlan(
        user_id=current_user.id,
        title=req.title,
        days=req.days,
        crowd_type=req.crowd_type,
        preferences=req.preferences,
        plan_content=req.plan_content,
        status="draft",
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return success({"id": plan.id})


@router.put("/plans/{plan_id}")
async def update_trip_plan(
    plan_id: int,
    req: TripPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新已有行程（草稿升级为正式方案、修改标题/内容等）。"""
    plan = (await db.execute(
        select(TripPlan).where(TripPlan.id == plan_id, TripPlan.user_id == current_user.id)
    )).scalar()
    if not plan:
        raise HTTPException(status_code=404, detail="行程不存在")
    if req.title is not None:
        plan.title = req.title
    if req.plan_content is not None:
        plan.plan_content = req.plan_content
    if req.status is not None:
        plan.status = req.status
    await db.flush()
    await db.refresh(plan)
    return success(TripPlanOut.model_validate(plan).model_dump())


@router.get("/plans")
async def list_trip_plans(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """获取用户的行程计划列表。"""
    q = select(TripPlan).where(TripPlan.user_id == current_user.id)
    count_q = select(func.count(TripPlan.id)).where(TripPlan.user_id == current_user.id)

    if status:
        q = q.where(TripPlan.status == status)
        count_q = count_q.where(TripPlan.status == status)

    q = q.order_by(desc(TripPlan.created_at))
    offset = (page - 1) * page_size
    q = q.offset(offset).limit(page_size)

    total = (await db.execute(count_q)).scalar()
    rows = (await db.execute(q)).scalars().all()
    items = [TripPlanOut.model_validate(r).model_dump() for r in rows]

    return paginated(items, total, page, page_size)


@router.get("/plans/{plan_id}")
async def get_trip_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个行程详情。"""
    plan = (await db.execute(
        select(TripPlan).where(TripPlan.id == plan_id, TripPlan.user_id == current_user.id)
    )).scalar()
    if not plan:
        raise HTTPException(status_code=404, detail="行程不存在")
    return success(TripPlanOut.model_validate(plan).model_dump())


@router.delete("/plans/{plan_id}")
async def delete_trip_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除行程计划。"""
    plan = (await db.execute(
        select(TripPlan).where(TripPlan.id == plan_id, TripPlan.user_id == current_user.id)
    )).scalar()
    if not plan:
        raise HTTPException(status_code=404, detail="行程不存在")
    await db.delete(plan)
    await db.flush()
    return success(message="行程已删除")


# --- 占位行程生成 ---
def _generate_plan(days: int, preferences: list[str], crowd_type: str) -> dict:
    """生成降级行程模板 — 支持任意天数，动态填充。"""
    prefs = preferences if preferences else ["美食", "非遗"]
    crowd_label = {"solo": "独自旅行", "couple": "情侣出游", "family": "家庭出游", "friends": "朋友结伴"}

    # 模板池 — 可循环复用
    template_pool = [
        {
            "title": "汕头老城 · 美食初探",
            "spots": [
                {"name": "小公园骑楼群", "type": "景点", "duration": "1.5小时", "tip": "拍摄骑楼最佳时间在上午"},
                {"name": "八合里海记牛肉火锅", "type": "美食", "duration": "1小时", "tip": "吊龙和匙柄是必点"},
                {"name": "西堤公园", "type": "景点", "duration": "1小时", "tip": "傍晚看日落位置绝佳"},
            ],
        },
        {
            "title": "潮州古城 · 非遗之旅",
            "spots": [
                {"name": "广济桥（湘子桥）", "type": "景点", "duration": "1.5小时", "tip": "中国四大古桥之一"},
                {"name": "潮州工夫茶体验馆", "type": "体验", "duration": "1.5小时", "tip": "学习二十一式冲泡法"},
                {"name": "牌坊街", "type": "街区", "duration": "2小时", "tip": "品尝地道小吃：蚝烙、鸭母捻"},
            ],
        },
        {
            "title": "南澳岛 · 海岛风光",
            "spots": [
                {"name": "青澳湾", "type": "景点", "duration": "2小时", "tip": "广东最美的海湾之一"},
                {"name": "南澳总兵府", "type": "历史", "duration": "1小时", "tip": "明清海防重地"},
                {"name": "海鲜大排档", "type": "美食", "duration": "1.5小时", "tip": "现捞现做，推荐海胆炒饭"},
            ],
        },
        {
            "title": "揭阳古城 · 民俗探秘",
            "spots": [
                {"name": "揭阳学宫", "type": "景点", "duration": "1小时", "tip": "岭南地区保存最完整的学宫"},
                {"name": "城隍庙", "type": "景点", "duration": "40分钟", "tip": "潮汕香火最旺的庙宇之一"},
                {"name": "揭阳肠粉", "type": "美食", "duration": "45分钟", "tip": "酱汁浓稠，口感独特"},
            ],
        },
        {
            "title": "潮汕深度 · 文化沉浸",
            "spots": [
                {"name": "龙湖古寨", "type": "景点", "duration": "2小时", "tip": "千年古寨，潮汕民居活化石"},
                {"name": "英歌舞表演", "type": "体验", "duration": "1小时", "tip": "提前查询演出时间和地点"},
                {"name": "潮菜私房菜馆", "type": "美食", "duration": "1.5小时", "tip": "正宗潮菜，需提前预约"},
            ],
        },
    ]

    day_plans = []
    for i in range(days):
        tmpl = template_pool[i % len(template_pool)]
        day_plans.append({"day": i + 1, "title": tmpl["title"], "spots": tmpl["spots"]})

    return {
        "days": day_plans,
        "crowd_label": crowd_label.get(crowd_type, "自由行"),
        "preferences": prefs,
        "_offline": True,
        "tips": [
            "⚠️ 当前为离线演示方案，部分信息可能不准确",
            "潮汕地区秋冬季节（10月-次年4月）是最佳旅游时间",
            "牛肉火锅建议午餐去，牛肉最新鲜",
            "部分非遗体验项目需提前预约",
        ],
    }
