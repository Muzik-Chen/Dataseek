"""
行程规划 Agent — 多 Agent LangGraph 管道 + SSE 流式输出。

Phase 6: 5 节点 LangGraph 管道（food_agent + hotel_agent 并行执行）：
    orchestrator_plan → route_agent → [food_agent ‖ hotel_agent] → orchestrator_merge

外循环：对 A/B/C 三套方案各跑一次管道，每步增量 yield trip_card。
管道结束后，调用 route_enricher 补充天气/人流/非遗/geo。

SSE 事件顺序（每套方案）：
    thinking → trip_card(orchestrator) → trip_card(route)
    → trip_card(food) ‖ trip_card(hotel) → trip_card(merge) → trip_card(enriched) → route_* events
"""
import json
import asyncio
from typing import AsyncGenerator

from ai.llm import get_llm
from ai.prompts import NARRATOR_PROMPT, PLAN_THEMES, sse_event
from config import get_settings


# ═══════════════════════════════════════════
# 辅助：从 TripState 构建增量 plan dict
# ═══════════════════════════════════════════

def _build_partial_plan(state: dict) -> dict:
    """从当前 TripState 构建可渲染的 plan dict（供前端 TripCard 增量渲染）。

    每步 Agent 完成后调用，构建的 plan 会被前端浅合并到同名 plan_id。
    food_agent 和 hotel_agent 并行执行，各自完成即产出增量 patch。
    """
    plan_id = state.get("plan_id", "?")
    framework = state.get("route_framework") or {}
    route = state.get("route_detail") or {}
    foods = state.get("food_recommendations") or {}
    hotels = state.get("hotel_recommendations") or {}
    merged = state.get("merged_plan") or {}

    # 优先使用 merged_plan（最终版），否则逐级构建
    if merged:
        return merged

    plan = {
        "plan_id": plan_id,
        "title": f"方案{plan_id}",
        "theme": state.get("theme", ""),
        "summary": framework.get("city_flow", ""),
    }

    # 逐级加入已有数据
    if route:
        plan["transport"] = route.get("transport")
        # 深拷贝 days，避免修改原始 state
        plan["days"] = _deep_copy_days(route.get("days", []))

    if hotels.get("hotels"):
        plan["hotels"] = hotels["hotels"]

    if foods.get("recommendations") and plan.get("days"):
        # 将 food recommendations 注入到对应天的最近 activity
        _inject_foods_into_days(plan["days"], foods.get("recommendations", []))
        plan["foods_summary"] = foods.get("foods_summary", "")

    return plan


def _deep_copy_days(days: list) -> list:
    """深拷贝 days 结构（activities 级别），避免修改 state 中的原始数据。"""
    import copy
    return copy.deepcopy(days)


def _inject_foods_into_days(days: list, recommendations: list):
    """将美食推荐注入到每天的最近 activity 中。

    策略：午餐时段(11:00-14:00)注入到当天中段的 activity，
         晚餐时段(17:00-20:00)注入到当天最后的 activity。
         不依赖 activity.type == "food"。
    """
    # 构建 day→meal→foods 映射
    food_map: dict = {}
    for rec in recommendations:
        day = rec.get("day", 0)
        meal = rec.get("meal", "lunch")
        key = f"{day}_{meal}"
        food_map[key] = rec.get("foods", [])

    for d in days:
        day_num = d.get("day", 1)
        activities = d.get("activities", [])
        if not activities:
            continue

        n = len(activities)

        # 午餐：注入到第 floor(n/3) 个 activity（前段偏中）
        lunch_foods = food_map.get(f"{day_num}_lunch", [])
        if lunch_foods and n > 0:
            lunch_idx = min(n // 3, n - 1)
            if not activities[lunch_idx].get("nearby_foods"):
                activities[lunch_idx]["nearby_foods"] = _format_nearby_foods(lunch_foods)

        # 晚餐：注入到第 floor(2n/3) 个 activity（后段偏中）
        dinner_foods = food_map.get(f"{day_num}_dinner", [])
        if dinner_foods and n > 0:
            dinner_idx = min(2 * n // 3, n - 1)
            if dinner_idx == lunch_idx and n > 1:
                dinner_idx = min(dinner_idx + 1, n - 1)  # 避免与午餐冲突
            if not activities[dinner_idx].get("nearby_foods"):
                activities[dinner_idx]["nearby_foods"] = _format_nearby_foods(dinner_foods)


def _format_nearby_foods(foods: list) -> list:
    """格式化 nearby_foods 为前端 TripCard 兼容格式。"""
    return [
        {"food_id": f.get("food_id"), "name": f.get("name"),
         "price": f.get("price", ""), "reason": f.get("reason", ""),
         "tags": f.get("tags", [])}
        for f in foods
    ]


# ═══════════════════════════════════════════
# SSE 流式主入口
# ═══════════════════════════════════════════

async def generate_trip_plans_stream(
    params: dict,
    interest_hints: list[str] | None = None,
) -> AsyncGenerator[str, None]:
    """流式生成 3 套旅行方案 — SSE 事件流生成器（Phase 6 LangGraph 版）。

    输出顺序：
    1. thinking + token 事件 — 流式开场白
    2. 对每套方案 (A/B/C):
       a. graph.astream() → 每个节点完成后 yield trip_card 增量 patch
       b. route_enricher → yield trip_card (最终富化版) + route_* 事件
    3. token 事件 — 结尾语
    4. 由调用方发送 done 事件

    Args:
        params: {origin, days, crowd_type, interests, budget}
        interest_hints: Phase 2 — 用户兴趣关键词，用于 route_enricher 匹配

    Yields:
        SSE 格式的事件字符串
    """
    settings = get_settings()

    # === Step 1: 流式开场白 ===
    try:
        narrator_llm = get_llm(temperature=0.8, streaming=True, request_timeout=30)
        narrator_prompt = NARRATOR_PROMPT.format(
            origin=params.get("origin", ""),
            days=params.get("days", 3),
            crowd_type={"solo": "独自旅行", "couple": "情侣出游",
                        "family": "家庭出游", "friends": "朋友结伴",
                        "single": "独自旅行"}.get(params.get("crowd_type", ""), "自由行"),
            interests="、".join(params.get("interests", [])),
        )

        yield sse_event("thinking", label="正在为您规划潮汕旅行方案...")

        async for chunk in narrator_llm.astream(narrator_prompt):
            token = chunk.content if hasattr(chunk, "content") else str(chunk)
            if token:
                yield sse_event("token", content=token)
                await asyncio.sleep(0)

        yield sse_event("token", content="\n\n")
        await asyncio.sleep(0)

    except Exception as e:
        print(f"[TripAgent] Narrator failed: {e}")
        yield sse_event("thinking", label="正在为您规划3套旅行方案...")

    # === Step 2: 管道循环 ×3 ===
    from ai.trip_graph import TripState, get_trip_graph

    graph = get_trip_graph()
    completed_count = 0

    for idx, theme_info in enumerate(PLAN_THEMES):
        plan_id = theme_info["plan_id"]

        initial_state: TripState = {
            "origin": params.get("origin", ""),
            "days": params.get("days", 3),
            "crowd_type": params.get("crowd_type", "solo"),
            "interests": params.get("interests", []),
            "budget": params.get("budget", "mid"),
            "theme": theme_info["desc"],
            "plan_id": plan_id,
            "route_framework": None,
            "route_detail": None,
            "food_recommendations": None,
            "hotel_recommendations": None,
            "merged_plan": None,
            "error": None,
        }

        yield sse_event("thinking", label=f"开始生成方案{plan_id}...")

        try:
            # 流式执行图 — 每个节点完成后回调
            async for event in graph.astream(initial_state, stream_mode="updates"):
                node_name = list(event.keys())[0]
                node_output = event[node_name]

                # 更新 state（手动累积，因为 stream_mode="updates" 只返回 delta）
                for k, v in node_output.items():
                    if k in initial_state:
                        initial_state[k] = v

                if node_name == "orchestrator_plan":
                    yield sse_event("thinking", label=f"方案{plan_id}路线框架已生成，正在规划具体路线...")
                    yield sse_event("trip_card", plan=_build_partial_plan(initial_state))

                elif node_name == "route_agent":
                    yield sse_event("thinking", label=f"方案{plan_id}路线已规划，正在同步查询美食与酒店...")
                    yield sse_event("trip_card", plan=_build_partial_plan(initial_state))

                elif node_name == "food_agent":
                    yield sse_event("trip_card", plan=_build_partial_plan(initial_state))
                    # 如果酒店也已完成，提示即将合并
                    if initial_state.get("hotel_recommendations"):
                        yield sse_event("thinking", label=f"方案{plan_id}美食与酒店已就绪，正在生成完整方案...")

                elif node_name == "hotel_agent":
                    yield sse_event("trip_card", plan=_build_partial_plan(initial_state))
                    # 如果美食也已完成，提示即将合并
                    if initial_state.get("food_recommendations"):
                        yield sse_event("thinking", label=f"方案{plan_id}美食与酒店已就绪，正在生成完整方案...")

                elif node_name == "orchestrator_merge":
                    plan = initial_state.get("merged_plan") or _build_partial_plan(initial_state)

                    if plan and not plan.get("error"):
                        completed_count += 1
                        plan["_index"] = completed_count
                        plan["_total"] = 3

                        # 先发基础版 trip_card
                        yield sse_event("thinking", label=f"方案{plan_id}已完成，正在加载周边信息...")
                        yield sse_event("trip_card", plan=plan)

                        # enricher (天气/人流/非遗/geo)
                        if settings.ENABLE_ROUTE_ENRICHER:
                            try:
                                from ai.route_enricher import enrich_plan
                                enrichment = await asyncio.wait_for(
                                    enrich_plan(plan, interest_hints), timeout=8.0
                                )
                                plan["enrichment"] = enrichment["enrichment"]
                                plan["route_geo"] = enrichment["route_geo"]
                                yield sse_event("trip_card", plan=plan)

                                # route_* 明细事件
                                enrich = enrichment["enrichment"]
                                pid = plan.get("plan_id")
                                if enrich.get("weather"):
                                    yield sse_event("route_weather", plan_id=pid, weather=enrich["weather"])
                                if enrich.get("foods"):
                                    yield sse_event("route_foods", plan_id=pid, foods=enrich["foods"])
                                if enrich.get("heritages"):
                                    yield sse_event("route_heritages", plan_id=pid, heritages=enrich["heritages"])
                                if enrich.get("hotels"):
                                    yield sse_event("route_hotels", plan_id=pid, hotels=enrich["hotels"])
                                if enrich.get("crowd"):
                                    yield sse_event("route_crowd", plan_id=pid, crowd=enrich["crowd"])
                            except (asyncio.TimeoutError, Exception) as e:
                                print(f"[TripAgent] Route enricher failed for plan {plan_id}: {e}")
                    else:
                        print(f"[TripAgent] Plan {plan_id} merge returned error or empty plan")
                        yield sse_event("plan_failed", theme_id=plan_id, theme=theme_info["theme"],
                                       error=initial_state.get("error", "merge 节点返回空"))

        except Exception as e:
            print(f"[TripAgent] Graph execution failed for plan {plan_id}: {e}")
            yield sse_event("plan_failed", theme_id=plan_id, theme=theme_info["theme"],
                           error=str(e)[:120])

    # === Step 3: 结尾语 ===
    if completed_count == 0:
        yield sse_event("error", message="所有方案生成失败，请检查 LLM API 配置或稍后重试")
    elif completed_count < 3:
        yield sse_event("token",
                   content=f"\n\n以上是成功生成的 {completed_count} 套方案（共 3 套），"
                           f"部分方案因网络波动未能完成，您可以重新发起规划。")
    else:
        yield sse_event("token", content="\n\n以上是 3 套方案，各有侧重。您可以根据自己的偏好选择最心仪的一套，也可以告诉我需要调整的地方哦！")


# ═══════════════════════════════════════════
# 向后兼容：同步版本
# ═══════════════════════════════════════════

async def generate_three_plans(params: dict) -> list[dict]:
    """同步生成 3 套方案（向后兼容）。

    注意：推荐使用 generate_trip_plans_stream() 以获得流式体验。
    """
    results = []
    async for event_str in generate_trip_plans_stream(params):
        if "trip_card" in event_str:
            try:
                line = event_str.strip()
                if line.startswith("data: "):
                    payload = json.loads(line[6:])
                    if payload.get("type") == "trip_card" and payload.get("plan"):
                        plan = payload["plan"]
                        plan_id = plan.get("plan_id", "")
                        # 同名 plan_id 覆盖（取最后版本即 enriched 版）
                        existing = next((r for r in results if r.get("plan_id") == plan_id), None)
                        if existing:
                            results[results.index(existing)] = plan
                        else:
                            results.append(plan)
            except json.JSONDecodeError:
                pass
    return results


# ═══════════════════════════════════════════
# LangGraph 包装（向后兼容）
# ═══════════════════════════════════════════

def create_trip_graph():
    """创建行程规划 StateGraph（委托给 trip_graph 模块）。"""
    from ai.trip_graph import create_trip_graph as _create
    return _create()


# 全局单例
_trip_app = None


def get_trip_app():
    """获取编译后的 TripGraph 单例。"""
    global _trip_app
    if _trip_app is None:
        _trip_app = create_trip_graph()
    return _trip_app
