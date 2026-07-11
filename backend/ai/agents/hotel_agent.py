"""
Hotel Agent — 住宿推荐专业 Agent（两阶段：工具采集 + JSON 格式化）。

Phase 1: 使用 low-tier 模型 + tool calling 从 DB 收集真实酒店数据
Phase 2: 使用 high-tier 模型 + response_format=json_object 生成带 reasoning 文案的结构化 JSON

关键：Phase 2 强制 JSON 输出，保证每家酒店都有专业的推荐理由。
"""
import json
import asyncio

from ai.llm import get_llm
from ai.agent_tools import HOTEL_TOOLS
from ai.prompts.utils import clean_json


# ── Phase 1 Prompt: 工具调用采集数据 ──

HOTEL_SEARCH_PROMPT = """你是一位住宿数据采集助手。请使用工具搜索酒店数据。

## 住宿约束
{hotel_constraints}

## 核心区域坐标（取每天第一个景点的坐标）
{core_coords}

## 预算
{budget}

## 任务
1. 对每个核心坐标，调用 search_hotels_by_location 搜索周边 3km 的酒店
2. 如果结果不足，用 search_hotels_by_stars 按星级补充搜索
3. 搜索完毕后说"数据采集完成"

**每条搜索结果都会保存，你不用输出最终 JSON，只需调用工具采集数据。**"""


# ── Phase 2 Prompt: 强制 JSON 格式化（带 reasoning 文案）──

HOTEL_FORMAT_PROMPT = """你是一位资深酒店测评师。以下是工具从数据库中查询到的真实酒店数据。

请基于这些**真实数据**，为旅行者推荐 3 家酒店（经济/舒适/奢华各 1 家），并为每家撰写专业的推荐理由。

## 真实酒店数据（来自数据库）
{tool_results}

## 住宿约束
{hotel_constraints}

## 行程概览
{route_summary}

## 预算
{budget}
- low:  经济型，推荐 2-3 星，价格 100-200 元/晚
- mid:  舒适型，推荐 3-4 星，价格 200-500 元/晚
- high: 豪华型，推荐 4-5 星，价格 500+ 元/晚

## 要求
1. 筛选 3 档各 1 家：budget（经济）、comfort（舒适）、luxury（奢华）
2. reason 字段要具体：位置优势、与景点的距离、适合人群、特色服务
3. 输出严格的 JSON 格式（不要 markdown 代码块）

输出格式：
{{
  "hotels": [
    {{
      "name": "酒店全名",
      "stars": 4,
      "price": 350,
      "level": "comfort",
      "lat": 23.358,
      "lng": 116.670,
      "reason": "位于老城核心区，步行5分钟可达汕头小公园，房间可眺望骑楼街景，适合情侣入住"
    }}
  ]
}}"""


# ═══════════════════════════════════════════
# 节点函数
# ═══════════════════════════════════════════

async def hotel_agent_node(state: dict) -> dict:
    """酒店推荐节点 — 两阶段：工具采集 + JSON 格式化。

    输入：state["route_framework"]["hotel_constraints"], state["route_detail"]
    输出 → state["hotel_recommendations"]
    """
    framework = state.get("route_framework", {}) or {}
    hotel_constraints = framework.get("hotel_constraints", {})
    route_detail = state.get("route_detail", {})
    budget = state.get("budget", "mid")

    # 提取核心坐标
    core_coords = _extract_core_coords(route_detail)

    # ── Phase 1: 工具调用采集数据 (low-tier, 快速) ──
    tool_results = await _collect_hotel_data(hotel_constraints, core_coords, budget)

    if not tool_results:
        print("[HotelAgent] 工具未采集到数据，返回空结果")
        return {"hotel_recommendations": _empty_hotel_result()}

    # ── Phase 2: JSON 格式化 (high-tier, 强制 JSON) ──
    hotel_recs = await _format_hotel_json(tool_results, hotel_constraints, route_detail, budget)

    return {"hotel_recommendations": hotel_recs}


# ═══════════════════════════════════════════
# Phase 1: 数据采集
# ═══════════════════════════════════════════

async def _collect_hotel_data(hotel_constraints: dict, core_coords: list[dict], budget: str) -> list[dict]:
    """工具调用阶段 — 使用 low-tier 模型驱动工具，收集真实酒店数据。"""
    from langchain_core.messages import HumanMessage

    llm = get_llm(temperature=0.2, streaming=False, request_timeout=60,
                  max_tokens=2048, reasoning_level="low")
    llm_with_tools = llm.bind_tools(HOTEL_TOOLS)

    prompt = HOTEL_SEARCH_PROMPT.format(
        hotel_constraints=json.dumps(hotel_constraints, ensure_ascii=False),
        core_coords=json.dumps(core_coords, ensure_ascii=False),
        budget=budget,
    )

    messages = [HumanMessage(content=prompt)]
    seen_calls = set()

    try:
        for round_num in range(3):  # 最多 3 轮数据采集
            response = await asyncio.wait_for(
                llm_with_tools.ainvoke(messages), timeout=60
            )

            if hasattr(response, "tool_calls") and response.tool_calls:
                # 重复检测
                round_sigs = set()
                for tc in response.tool_calls:
                    sig = (tc.get("name", ""), json.dumps(tc.get("args", {}), sort_keys=True))
                    round_sigs.add(sig)
                if round_sigs.issubset(seen_calls):
                    break
                seen_calls.update(round_sigs)

                messages.append(response)
                for tool_call in response.tool_calls:
                    tool_name = tool_call.get("name", "")
                    tool_args = tool_call.get("args", {})
                    tool_id = tool_call.get("id", "")

                    tool_func = {t.name: t for t in HOTEL_TOOLS}.get(tool_name)
                    if tool_func:
                        try:
                            result = await tool_func.ainvoke(tool_args)
                            from langchain_core.messages import ToolMessage
                            messages.append(ToolMessage(
                                content=json.dumps(result, ensure_ascii=False),
                                tool_call_id=tool_id,
                            ))
                        except Exception as e:
                            print(f"[HotelAgent] Tool {tool_name} 执行失败: {e}")
                            from langchain_core.messages import ToolMessage
                            messages.append(ToolMessage(
                                content=json.dumps({"error": str(e)}),
                                tool_call_id=tool_id,
                            ))
            else:
                break
    except asyncio.TimeoutError:
        print("[HotelAgent] 工具调用超时")
    except Exception as e:
        print(f"[HotelAgent] 工具调用异常: {e}")

    # 提取所有 ToolMessage 中的结果
    from langchain_core.messages import ToolMessage
    all_results = []
    seen_ids = set()
    for msg in messages:
        if isinstance(msg, ToolMessage):
            try:
                data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                items = data if isinstance(data, list) else ([data] if isinstance(data, dict) else [])
                for item in items:
                    hid = item.get("hotel_id") or item.get("id")
                    if hid and hid not in seen_ids:
                        seen_ids.add(hid)
                        all_results.append(item)
            except (json.JSONDecodeError, TypeError):
                pass

    return all_results


# ═══════════════════════════════════════════
# Phase 2: JSON 格式化（强制 response_format）
# ═══════════════════════════════════════════

async def _format_hotel_json(tool_results: list[dict], hotel_constraints: dict,
                              route_detail: dict, budget: str) -> dict:
    """格式化阶段 — 使用 high-tier 模型 + response_format=json_object 生成最终 JSON。"""
    from langchain_core.messages import HumanMessage

    llm = get_llm(
        temperature=0.4,
        streaming=False,
        request_timeout=60,
        max_tokens=2048,
        reasoning_level="high",
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    # 提取行程摘要（仅关键信息）
    days_summary = []
    for d in (route_detail.get("days", []) or [])[:3]:
        acts = [a.get("name", "") for a in (d.get("activities", []) or [])[:3]]
        days_summary.append(f"Day{d.get('day', '?')}: {', '.join(acts)}")

    # 精简 tool_results：每条只保留关键字段
    slim_results = []
    for r in tool_results[:15]:
        slim_results.append({
            "hotel_id": r.get("hotel_id"),
            "name": r.get("name"),
            "stars": r.get("stars"),
            "price_min": r.get("price_min"),
            "price_max": r.get("price_max"),
            "distance_km": r.get("distance_km"),
            "tags": r.get("tags", [])[:3],
            "address": r.get("address", "")[:40],
            "region": r.get("region", ""),
        })

    prompt = HOTEL_FORMAT_PROMPT.format(
        tool_results=json.dumps(slim_results, ensure_ascii=False),
        hotel_constraints=json.dumps(hotel_constraints, ensure_ascii=False)[:800],
        route_summary="\n".join(days_summary) if days_summary else "无行程信息",
        budget=budget,
    )

    try:
        response = await asyncio.wait_for(llm.ainvoke([HumanMessage(content=prompt)]), timeout=60)
        content = response.content if hasattr(response, "content") else str(response)
        return json.loads(str(content))
    except asyncio.TimeoutError:
        print("[HotelAgent] JSON 格式化超时")
    except json.JSONDecodeError as e:
        print(f"[HotelAgent] JSON 解析失败: {e}")
        raw = str(response.content) if hasattr(response, "content") else ""
        cleaned = clean_json(raw)
        if cleaned:
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"[HotelAgent] JSON 格式化异常: {e}")

    return _build_hotel_fallback(tool_results)


# ═══════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════

def _extract_core_coords(route_detail: dict) -> list[dict]:
    """从 route_detail 中提取每天第一个景点的坐标作为核心区域坐标。"""
    coords = []
    for d in (route_detail.get("days", []) or []):
        activities = d.get("activities", []) or []
        for a in activities:
            lat = a.get("lat")
            lng = a.get("lng")
            if lat and lng:
                coords.append({
                    "day": d.get("day", 1),
                    "name": a.get("name", ""),
                    "lat": lat,
                    "lng": lng,
                })
                break  # 每天只取第一个有坐标的活动
    return coords


def _build_hotel_fallback(tool_results: list[dict]) -> dict:
    """从 tool 结果直接构建推荐（无 LLM reasoning 的最后降级）。"""
    if not tool_results:
        return _empty_hotel_result()

    levels = ["budget", "comfort", "luxury"]
    result_hotels = []
    for i, h in enumerate(tool_results[:3]):
        price = h.get("price_min") or h.get("price", 300)
        stars = h.get("stars", 3)
        result_hotels.append({
            "name": h.get("name", "未知酒店"),
            "stars": stars,
            "price": price,
            "level": levels[i] if i < len(levels) else "comfort",
            "lat": h.get("lat", 23.358),
            "lng": h.get("lng", 116.670),
            "reason": f"距核心区域{h.get('distance_km', '?')}km · {stars}星级 · {'，'.join(h.get('tags', ['位置便利']))}",
        })

    return {"hotels": result_hotels}


def _empty_hotel_result() -> dict:
    return {"hotels": []}
