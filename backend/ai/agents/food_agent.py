"""
Food Agent — 美食推荐专业 Agent（两阶段：工具采集 + JSON 格式化）。

Phase 1: 使用 low-tier 模型 + tool calling 从 DB 收集真实美食数据
Phase 2: 使用 high-tier 模型 + response_format=json_object 生成带 reasoning 文案的结构化 JSON

关键：Phase 2 强制 JSON 输出，保证每条推荐都有人性化的 reason 字段。
"""
import json
import asyncio

from ai.llm import get_llm
from ai.agent_tools import FOOD_TOOLS
from ai.prompts.utils import clean_json


# ── Phase 1 Prompt: 工具调用采集数据 ──

FOOD_SEARCH_PROMPT = """你是一位潮汕美食数据采集助手。请使用工具搜索餐厅数据。

## 每日行程景点（含坐标）
{route_detail}

## 美食偏好
{food_constraints}

## 任务
对每一天的午餐(12:00)和晚餐(18:00)，使用工具搜索景点周边 3km 内的餐厅：
1. 对每天核心景点调用 search_foods_by_location 搜索周边
2. 如有特殊偏好（如"牛肉火锅"），用 search_foods_by_type 补充
3. 搜索完毕后说"数据采集完成"

**每条搜索结果都会保存，你不用输出最终 JSON，只需调用工具采集数据。**"""


# ── Phase 2 Prompt: 强制 JSON 格式化（带 reasoning 文案）──

FOOD_FORMAT_PROMPT = """你是一位潮汕美食专家。以下是工具从数据库中查询到的真实餐厅数据，以及行程详情。

请基于这些**真实数据**，为行程中的每一餐推荐餐厅，并为每家餐厅撰写人性化的推荐理由。

## 真实餐厅数据（来自数据库）
{tool_results}

## 每日行程
{route_detail}

## 预算
{budget}

## 要求
1. 为每天推荐午餐(12:00)和晚餐(18:00)，每餐 2-3 家餐厅
2. reason 字段要有说服力：结合距离、口碑、与行程的匹配度
3. 优先选择距离景点近的餐厅
4. 输出严格的 JSON 格式（不要 markdown 代码块）

输出格式：
{{
  "recommendations": [
    {{
      "day": 1,
      "meal": "lunch",
      "foods": [
        {{
          "food_id": 5,
          "name": "八合里牛肉火锅",
          "price": "¥80/人",
          "reason": "距离上午最后一个景点步行仅5分钟，老字号品质保证，牛肉现切现涮",
          "tags": ["牛肉火锅", "老字号"]
        }}
      ]
    }}
  ],
  "foods_summary": "本次行程共推荐 X 家餐厅，涵盖牛肉火锅、海鲜排档、粿条小吃等潮汕经典美食，均位于景点步行范围内"
}}"""


# ═══════════════════════════════════════════
# 节点函数
# ═══════════════════════════════════════════

async def food_agent_node(state: dict) -> dict:
    """美食推荐节点 — 两阶段：工具采集 + JSON 格式化。

    输入：state["route_detail"], state["route_framework"]["food_constraints"]
    输出 → state["food_recommendations"]
    """
    route_detail = state.get("route_detail", {})
    framework = state.get("route_framework", {}) or {}
    food_constraints = framework.get("food_constraints", {})

    if not route_detail.get("days"):
        return {"food_recommendations": _empty_food_result()}

    # ── Phase 1: 工具调用采集数据 (low-tier, 快速) ──
    tool_results = await _collect_food_data(route_detail, food_constraints)

    if not tool_results:
        print("[FoodAgent] 工具未采集到数据，返回空结果")
        return {"food_recommendations": _empty_food_result()}

    # ── Phase 2: JSON 格式化 (high-tier, 强制 JSON) ──
    food_recs = await _format_food_json(tool_results, route_detail, state.get("budget", "mid"))

    return {"food_recommendations": food_recs}


# ═══════════════════════════════════════════
# Phase 1: 数据采集
# ═══════════════════════════════════════════

async def _collect_food_data(route_detail: dict, food_constraints: dict) -> list[dict]:
    """工具调用阶段 — 使用 low-tier 模型驱动工具，收集真实美食数据。"""
    from langchain_core.messages import HumanMessage

    llm = get_llm(temperature=0.2, streaming=False, request_timeout=60,
                  max_tokens=2048, reasoning_level="low")
    llm_with_tools = llm.bind_tools(FOOD_TOOLS)

    prompt = FOOD_SEARCH_PROMPT.format(
        route_detail=json.dumps(route_detail, ensure_ascii=False),
        food_constraints=json.dumps(food_constraints, ensure_ascii=False),
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

                    tool_func = {t.name: t for t in FOOD_TOOLS}.get(tool_name)
                    if tool_func:
                        try:
                            result = await tool_func.ainvoke(tool_args)
                            from langchain_core.messages import ToolMessage
                            messages.append(ToolMessage(
                                content=json.dumps(result, ensure_ascii=False),
                                tool_call_id=tool_id,
                            ))
                        except Exception as e:
                            print(f"[FoodAgent] Tool {tool_name} 执行失败: {e}")
                            from langchain_core.messages import ToolMessage
                            messages.append(ToolMessage(
                                content=json.dumps({"error": str(e)}),
                                tool_call_id=tool_id,
                            ))
            else:
                # 模型认为数据够了
                break
    except asyncio.TimeoutError:
        print("[FoodAgent] 工具调用超时")
    except Exception as e:
        print(f"[FoodAgent] 工具调用异常: {e}")

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
                    fid = item.get("food_id")
                    if fid and fid not in seen_ids:
                        seen_ids.add(fid)
                        all_results.append(item)
            except (json.JSONDecodeError, TypeError):
                pass

    return all_results


# ═══════════════════════════════════════════
# Phase 2: JSON 格式化（强制 response_format）
# ═══════════════════════════════════════════

async def _format_food_json(tool_results: list[dict], route_detail: dict, budget: str) -> dict:
    """格式化阶段 — 使用 high-tier 模型 + response_format=json_object 生成最终 JSON。"""
    from langchain_core.messages import HumanMessage

    llm = get_llm(
        temperature=0.4,
        streaming=False,
        request_timeout=60,
        max_tokens=4096,
        reasoning_level="high",
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    # 精简 tool_results：每条只保留 LLM 需要的关键字段，减少 token 消耗
    slim_results = []
    for r in tool_results[:20]:  # 最多 20 条
        slim_results.append({
            "food_id": r.get("food_id"),
            "name": r.get("name"),
            "type": r.get("type"),
            "price_range": r.get("price_range"),
            "distance_km": r.get("distance_km"),
            "tags": r.get("tags", [])[:3],
            "address": r.get("address", "")[:30],
        })

    prompt = FOOD_FORMAT_PROMPT.format(
        tool_results=json.dumps(slim_results, ensure_ascii=False),
        route_detail=json.dumps(route_detail, ensure_ascii=False)[:1500],
        budget=budget,
    )

    try:
        response = await asyncio.wait_for(llm.ainvoke([HumanMessage(content=prompt)]), timeout=60)
        content = response.content if hasattr(response, "content") else str(response)
        return json.loads(str(content))
    except asyncio.TimeoutError:
        print("[FoodAgent] JSON 格式化超时")
    except json.JSONDecodeError as e:
        print(f"[FoodAgent] JSON 解析失败: {e}")
        raw = str(response.content) if hasattr(response, "content") else ""
        cleaned = clean_json(raw)
        if cleaned:
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"[FoodAgent] JSON 格式化异常: {e}")

    # 最终降级：从 tool results 直接构建
    return _build_food_fallback(tool_results, route_detail)


# ═══════════════════════════════════════════
# 降级方案
# ═══════════════════════════════════════════

def _build_food_fallback(tool_results: list[dict], route_detail: dict) -> dict:
    """从 tool 结果直接构建推荐（无 LLM reasoning 的最后降级）。"""
    if not tool_results:
        return _empty_food_result()

    days = route_detail.get("days", [])
    recommendations = []
    food_idx = 0
    for d in days:
        day_num = d.get("day", 1)
        for meal in ["lunch", "dinner"]:
            meal_foods = []
            for _ in range(2):
                if food_idx < len(tool_results):
                    f = tool_results[food_idx]
                    meal_foods.append({
                        "food_id": f.get("food_id"),
                        "name": f.get("name", ""),
                        "price": f.get("price_range", "¥"),
                        "reason": f"距景点{f.get('distance_km', '?')}km · {'，'.join(f.get('tags', ['本地特色']))}",
                        "tags": f.get("tags", []),
                    })
                    food_idx += 1
            if meal_foods:
                recommendations.append({"day": day_num, "meal": meal, "foods": meal_foods})

    return {
        "recommendations": recommendations,
        "foods_summary": f"共推荐 {len(tool_results)} 家餐厅（数据库实时查询）",
    }


def _empty_food_result() -> dict:
    return {"recommendations": [], "foods_summary": "暂无美食推荐"}
