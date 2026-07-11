"""
Refinement Agent — 用户对已生成方案提出修改意见 → AI 流式返回调整后方案。

SSE 事件输出：
  thinking → token → trip_card（单个） → route_* → done
"""
import json
import asyncio
from typing import AsyncGenerator

from ai.llm import get_llm
from ai.prompts import REFINE_PROMPT, clean_json, repair_json, sse_event
from config import get_settings


async def refine_plan_stream(plan: dict, user_request: str) -> AsyncGenerator[str, None]:
    """流式调整旅行方案 — SSE 事件流生成器。

    Args:
        plan: 原始 plan 对象（含 plan_id/enrichment/route_geo）
        user_request: 用户修改要求，如"把酒店换成便宜的"

    Yields:
        SSE 格式的事件字符串
    """
    settings = get_settings()
    plan_id = plan.get("plan_id", "X")
    original_json = json.dumps(plan, ensure_ascii=False, indent=2)

    llm = get_llm(temperature=0.6, streaming=False, request_timeout=180, max_tokens=4096,
                  model_kwargs={"response_format": {"type": "json_object"}})

    # Step 1: 流式 thinking
    yield sse_event("thinking", label=f"正在根据您的要求调整方案{plan_id}...")

    # Step 2: 构建 prompt 并生成
    prompt = REFINE_PROMPT.format(
        original_plan_json=original_json,
        user_request=user_request,
    )

    refined_plan = None
    for attempt in (1, 2):
        try:
            response = await asyncio.wait_for(llm.ainvoke(prompt), timeout=180)
            content = response.content if hasattr(response, "content") else str(response)

            if not content or not str(content).strip():
                if attempt == 1:
                    continue
                yield sse_event("error", message="AI 返回空内容，请重试")
                return

            raw = str(content)
            cleaned = clean_json(raw)
            if not cleaned:
                if attempt == 1:
                    continue
                yield sse_event("error", message="AI 输出解析失败，请重试")
                return

            try:
                refined_plan = json.loads(cleaned)
            except json.JSONDecodeError as direct_err:
                repaired = repair_json(cleaned)
                if repaired != cleaned:
                    try:
                        refined_plan = json.loads(repaired)
                    except json.JSONDecodeError:
                        if attempt == 1:
                            prompt = (
                                f"⚠️ 上一次输出的 JSON 格式错误，请严格输出合法 JSON。\n\n"
                                + prompt
                            )
                            continue
                        yield sse_event("error", message=f"JSON 解析失败: {str(direct_err)[:60]}")
                        return
                else:
                    if attempt == 1:
                        prompt = (
                            f"⚠️ 上一次输出的 JSON 格式错误：{direct_err}\n"
                            f"请严格输出合法 JSON，不要添加注释或非 JSON 文本。\n\n"
                            + prompt
                        )
                        continue
                    yield sse_event("error", message=f"JSON 解析失败: {str(direct_err)[:60]}")
                    return

            # Parse succeeded
            break

        except asyncio.TimeoutError:
            if attempt == 1:
                continue
            yield sse_event("error", message="调整超时，请重试")
            return
        except Exception as e:
            if attempt == 1:
                continue
            yield sse_event("error", message=f"调整失败: {str(e)[:80]}")
            return

    if refined_plan is None:
        yield sse_event("error", message="调整失败，请重试")
        return

    # 保留原 plan 的 plan_id 和 enrichment/route_geo（若修改不涉及地点变化则复用）
    refined_plan["plan_id"] = plan_id
    refined_plan["_refined"] = True

    # 检查是否需要重新 enrichment
    original_days = plan.get("days", [])
    new_days = refined_plan.get("days", [])
    locations_changed = _locations_changed(original_days, new_days)

    # Step 3: 流式 token 输出（精简版思考过程）
    yield sse_event("token", content=f"方案{plan_id}已按您的要求调整完成。")
    await asyncio.sleep(0)

    # Step 4: Route enrichment（若地点有变化）
    if locations_changed and settings.ENABLE_ROUTE_ENRICHER and not refined_plan.get("error"):
        try:
            from ai.route_enricher import enrich_plan
            enrichment = await asyncio.wait_for(
                enrich_plan(refined_plan, None),
                timeout=8.0,
            )
            refined_plan["enrichment"] = enrichment["enrichment"]
            refined_plan["route_geo"] = enrichment["route_geo"]

            yield sse_event("trip_card", plan=refined_plan)

            enrich = enrichment["enrichment"]
            if enrich.get("weather"):
                yield sse_event("route_weather", plan_id=plan_id, weather=enrich["weather"])
            if enrich.get("foods"):
                yield sse_event("route_foods", plan_id=plan_id, foods=enrich["foods"])
            if enrich.get("heritages"):
                yield sse_event("route_heritages", plan_id=plan_id, heritages=enrich["heritages"])
            if enrich.get("hotels"):
                yield sse_event("route_hotels", plan_id=plan_id, hotels=enrich["hotels"])
            if enrich.get("crowd"):
                yield sse_event("route_crowd", plan_id=plan_id, crowd=enrich["crowd"])
        except asyncio.TimeoutError:
            yield sse_event("trip_card", plan=refined_plan)
        except Exception as e:
            print(f"[RefineAgent] Route enricher failed: {e}")
            yield sse_event("trip_card", plan=refined_plan)
    else:
        # 复用原 enrichment（地点无变化）
        if not locations_changed:
            refined_plan["enrichment"] = plan.get("enrichment")
            refined_plan["route_geo"] = plan.get("route_geo")
        yield sse_event("trip_card", plan=refined_plan)


def _locations_changed(original_days: list, new_days: list) -> bool:
    """简单检测地点是否变化：比较 activity name 集合。"""
    def activity_names(days):
        names = set()
        for d in (days or []):
            for a in d.get("activities", []):
                if a.get("name"):
                    names.add(a["name"])
        return names

    orig = activity_names(original_days)
    new = activity_names(new_days)
    # 如果超过 30% 的活动名称不同，认为地点发生了变化
    if not orig:
        return True
    overlap = len(orig & new)
    return overlap / max(len(orig), 1) < 0.7
