"""
Orchestrator Agent — 战略规划 + 收尾合并。

两个节点:
    orchestrator_plan_node:  分析用户参数，制定战略级路线框架（不选具体景点）
    orchestrator_merge_node: 合并前 4 个 Agent 输出 → 完整 plan JSON + 费用 + 贴士

模型：glm-4-plus (reasoning_level="high")
"""
import json
import asyncio

from ai.llm import get_llm
from ai.prompts.utils import clean_json, repair_json


# ═══════════════════════════════════════════
# Prompt 模板
# ═══════════════════════════════════════════

ORCHESTRATOR_PLAN_PROMPT = """你是一位资深的旅行规划师，负责制定潮汕地区旅行的**战略框架**。

## 用户信息
- 出发地：{origin}
- 天数：{days} 天
- 出行人群：{crowd_type}
- 兴趣偏好：{interests}
- 预算档位：{budget}
- 方案主题：{theme}

## 你的任务
制定一个高层级的路线框架。**不要选具体景点和餐厅**，只做战略规划。

请输出 JSON 格式（不要加代码块标记）：

{{
  "city_flow": "从出发地到潮汕各城市的天数分配，如'深圳→汕头(2天)→潮州(1天)'",
  "day_themes": [
    {{
      "day": 1,
      "theme": "这一天的主题（如'抵达汕头，初探老城美食'）",
      "area": "核心活动区域（如'汕头老城区'/'南澳岛'/'潮州古城区'），必须是具体地名"
    }}
  ],
  "food_constraints": {{
    "prefer_types": ["推荐的美食类型，如'牛肉火锅'、'海鲜'、'粿条'"],
    "max_per_meal": 人均餐费上限(元)
  }},
  "hotel_constraints": {{
    "areas": ["优先住宿区域"],
    "stars_min": 最低星级,
    "budget_night": 每晚预算上限(元)
  }}
}}

## 约束
- day_themes 的 area 字段必须是具体地名（如"汕头老城区"），不是模糊描述
- 约束要可执行（max_per_meal 和 budget_night 写具体数字）
- budget 档位：low=经济(goods_min=2, budget_night=150, max_per_meal=40)
               mid=舒适(stars_min=3, budget_night=350, max_per_meal=80)
               high=奢华(stars_min=4, budget_night=800, max_per_meal=200)
- crowd_type 影响节奏：solo/couple/family/friends（家庭游节奏慢，独自游可紧凑）"""


ORCHESTRATOR_MERGE_PROMPT = """你是一位资深旅行编辑，负责将所有 Agent 的输出合并为一份完整、可读的行程方案。

## 输入数据

### 路线框架
{route_framework}

### 每日行程详情
{route_detail}

### 美食推荐
{food_recommendations}

### 酒店推荐
{hotel_recommendations}

## 方案元信息
- 方案 ID：{plan_id}
- 方案主题：{theme}
- 出发地：{origin}
- 天数：{days} 天
- 出行人群：{crowd_type}
- 预算档位：{budget}

## 你的任务
将所有信息合并为一份完整的行程方案 JSON。请输出 JSON 格式（不要加代码块标记）：

{{
  "plan_id": "{plan_id}",
  "title": "吸引人的方案标题，体现 theme",
  "theme": "{theme}",
  "summary": "100字以内的方案概述",
  "transport": {{
    "to": {{"type": "高铁", "from": "{origin}", "to": "潮汕站/汕头站", "duration": "约2h", "cost": "¥150/人"}},
    "return": {{"type": "高铁", "from": "潮汕站/汕头站", "to": "{origin}", "duration": "约2h", "cost": "¥150/人"}}
  }},
  "hotels": [
    {{
      "name": "酒店名",
      "stars": 4,
      "price": 350,
      "level": "budget/comfort/luxury 三选一",
      "reason": "推荐理由"
    }}
  ],
  "days": [
    {{
      "day": 1,
      "title": "每日标题",
      "activities": [
        {{
          "time": "09:00",
          "name": "活动名称",
          "type": "scenery/food/culture/transport",
          "lat": 23.357,
          "lng": 116.672,
          "description": "简短描述",
          "reason": "推荐理由",
          "nearby_foods": [{{"food_id": 1, "name": "餐厅名", "price": "¥80/人"}}],
          "nearby_hotel": "推荐住宿酒店名"
        }}
      ]
    }}
  ],
  "estimated_cost": {{
    "transport": 300,
    "hotel": 1050,
    "food": 720,
    "tickets": 150,
    "total": 2220
  }},
  "tips": ["出行贴士1", "出行贴士2", "出行贴士3"]
}}

## 合并规则
1. 从 route_detail 提取 transport + days.activities（保持原有结构）
2. 从 food_recommendations 提取 nearby_foods，注入到对应 day 的 activity
3. 从 hotel_recommendations 提取 3 档酒店（budget/comfort/luxury 各 1 家），注入 hotels 字段
4. 估算费用：使用真实酒店价格 + 真实餐费 + 交通费 + 门票估算
5. 出行贴士：基于 crowd_type（{crowd_type}）和天数（{days}天）生成 3-5 条实用建议
6. 确保所有经纬度字段（lat/lng）都已填充"""


# ═══════════════════════════════════════════
# 节点函数
# ═══════════════════════════════════════════

async def orchestrator_plan_node(state: dict) -> dict:
    """战略规划节点 — 分析参数，制定路线框架。

    输出 → state["route_framework"]
    """
    llm = get_llm(
        temperature=0.4,
        streaming=False,
        request_timeout=120,
        max_tokens=2048,
        model_kwargs={"response_format": {"type": "json_object"}},
        reasoning_level="high",
    )

    prompt = ORCHESTRATOR_PLAN_PROMPT.format(
        origin=state.get("origin", ""),
        days=state.get("days", 3),
        crowd_type={"solo": "独自旅行", "couple": "情侣出游",
                     "family": "家庭出游", "friends": "朋友结伴"}.get(
                         state.get("crowd_type", "solo"), "自由行"),
        interests="、".join(state.get("interests", [])) or "美食、文化",
        budget=state.get("budget", "mid"),
        theme=state.get("theme", ""),
    )

    try:
        response = await asyncio.wait_for(llm.ainvoke(prompt), timeout=120)
        content = response.content if hasattr(response, "content") else str(response)
        raw = str(content)
        cleaned = clean_json(raw)
        if cleaned:
            framework = json.loads(cleaned)
        else:
            raise ValueError("JSON extraction returned empty")
    except Exception as e:
        print(f"[Orchestrator:plan] LLM 调用失败: {e}")
        # 返回一个最基本的框架作为降级
        framework = _fallback_framework(state)

    return {"route_framework": framework}


async def orchestrator_merge_node(state: dict) -> dict:
    """合并节点 — 将各 Agent 输出合并为完整 plan JSON。

    输入：state 中所有前序 Agent 的输出
    输出 → state["merged_plan"]
    """
    llm = get_llm(
        temperature=0.3,
        streaming=False,
        request_timeout=120,
        max_tokens=4096,
        model_kwargs={"response_format": {"type": "json_object"}},
        reasoning_level="high",
    )

    prompt = ORCHESTRATOR_MERGE_PROMPT.format(
        route_framework=json.dumps(state.get("route_framework", {}), ensure_ascii=False),
        route_detail=json.dumps(state.get("route_detail", {}), ensure_ascii=False),
        food_recommendations=json.dumps(state.get("food_recommendations", {}), ensure_ascii=False),
        hotel_recommendations=json.dumps(state.get("hotel_recommendations", {}), ensure_ascii=False),
        plan_id=state.get("plan_id", "?"),
        theme=state.get("theme", ""),
        origin=state.get("origin", ""),
        days=state.get("days", 3),
        crowd_type=state.get("crowd_type", "solo"),
        budget=state.get("budget", "mid"),
    )

    try:
        response = await asyncio.wait_for(llm.ainvoke(prompt), timeout=120)
        content = response.content if hasattr(response, "content") else str(response)
        raw = str(content)
        cleaned = clean_json(raw)
        if cleaned:
            merged = json.loads(cleaned)
        else:
            raise ValueError("JSON extraction returned empty")
        # 确保 plan_id/theme 与输入一致
        merged["plan_id"] = state.get("plan_id", "?")
        merged["theme"] = state.get("theme", "")
        merged["_title"] = state.get("plan_id", "?")  # 兼容旧的 title 字段
    except Exception as e:
        print(f"[Orchestrator:merge] LLM 调用失败: {e}")
        merged = _fallback_merge(state)

    return {"merged_plan": merged}


# ═══════════════════════════════════════════
# 降级方案
# ═══════════════════════════════════════════

def _fallback_framework(state: dict) -> dict:
    """当 LLM 不可用时，生成最基本的路线框架。"""
    days = state.get("days", 3)
    city_flow = f"{state.get('origin', '出发地')}→汕头({max(1, days-1)}天)→潮州(1天)"
    return {
        "city_flow": city_flow,
        "day_themes": [
            {"day": d+1, "theme": f"潮汕文化探索第{d+1}天", "area": "汕头老城区" if d < days-1 else "潮州古城区"}
            for d in range(days)
        ],
        "food_constraints": {
            "prefer_types": state.get("interests", ["美食"]),
            "max_per_meal": 80,
        },
        "hotel_constraints": {
            "areas": ["汕头老城"],
            "stars_min": 3,
            "budget_night": 350,
        },
    }


def _fallback_merge(state: dict) -> dict:
    """当 LLM 不可用时，生成最基本的合并 plan。"""
    rd = state.get("route_detail", {}) or {}
    fr = state.get("food_recommendations", {}) or {}
    hr = state.get("hotel_recommendations", {}) or {}
    return {
        "plan_id": state.get("plan_id", "?"),
        "title": f"方案{state.get('plan_id', '?')}",
        "theme": state.get("theme", ""),
        "summary": f"{state.get('days', 3)}天潮汕{state.get('theme', '旅行')}方案",
        "transport": (rd.get("transport") or {"to": {}, "return": {}}),
        "hotels": (hr.get("hotels") or []),
        "days": (rd.get("days") or []),
        "estimated_cost": {"transport": 300, "hotel": 1050, "food": 720, "tickets": 150, "total": 2220},
        "tips": ["建议提前预订酒店", "潮汕夏季炎热，注意防晒", "品尝牛肉火锅推荐去八合里"],
    }
