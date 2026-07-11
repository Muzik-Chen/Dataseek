"""
Route Agent — 战术级景点选择 + 时间排布。

职责：基于 orchestrator_plan 的战略框架，选择具体景点、排时间、定交通。

模型：glm-4-plus (reasoning_level="high")
"""
import json
import asyncio

from ai.llm import get_llm
from ai.prompts.utils import clean_json


ROUTE_AGENT_PROMPT = """你是一位深谙潮汕地区的当地向导，负责为行程填充具体的景点和活动。

## 战略框架（来自规划师）
{route_framework}

## 用户信息
- 出发地：{origin}
- 天数：{days} 天
- 出行人群：{crowd_type}

## 你的任务
基于战略框架中的 day_themes 和 area，为每一天选择 3-4 个具体景点/活动，并排好时间。

请输出 JSON 格式（不要加代码块标记）：

{{
  "transport": {{
    "to": {{"type": "高铁", "from": "{origin}", "to": "潮汕站", "duration": "约2h", "cost": "¥150/人"}},
    "return": {{"type": "高铁", "from": "潮汕站", "to": "{origin}", "duration": "约2h", "cost": "¥150/人"}}
  }},
  "days": [
    {{
      "day": 1,
      "title": "每日标题（体现主题，如'老城漫步·舌尖上的汕头'）",
      "activities": [
        {{
          "time": "09:00",
          "name": "景点/活动名称（具体名称，如'小公园骑楼群'而非'老城区'）",
          "type": "scenery/food/culture/transport",
          "lat": 23.357,
          "lng": 116.672,
          "description": "1-2句话描述活动内容和亮点",
          "duration": "预计停留时长，如'2h'",
          "reason": "为什么选这个景点（与主题的关联）"
        }}
      ]
    }}
  ]
}}

## 景点参考（你可以用，也可以用自己的知识）
### 汕头
- 小公园骑楼群 (23.357, 116.672) — 百年商埠，南洋风情
- 南澳岛青澳湾 (23.450, 117.080) — 广东最美的海滩之一
- 礐石风景区 (23.340, 116.660) — 山海奇观，登高望远
- 陈慈黉故居 (23.420, 116.745) — 岭南第一侨宅
- 海滨长廊 (23.352, 116.685) — 汕头内海湾景观带
- 澄海塔山 (23.470, 116.760) — 潮汕文化主题景区

### 潮州
- 广济桥 (23.665, 116.648) — 中国四大古桥之一
- 牌坊街 (23.665, 116.643) — 潮州古城核心，美食+非遗一条街
- 开元寺 (23.666, 116.644) — 唐代古刹，粤东第一丛林
- 韩文公祠 (23.667, 116.656) — 纪念韩愈，俯瞰韩江
- 己略黄公祠 (23.664, 116.642) — 潮州木雕艺术殿堂
- 龙湖古寨 (23.610, 116.690) — 千年古村落

### 揭阳
- 揭阳学宫 (23.548, 116.370) — 岭南三大学宫之一
- 揭阳城隍庙 (23.547, 116.372) — 潮汕最大城隍庙

## 约束
- 每天 3-4 个活动，类型要多样（scenery/food/culture 交替）
- 动线合理：相邻景点的经纬度不要跨城市
- 每项活动都填好 lat/lng（参考上面坐标，或基于地理知识估算）
- 上午 9:00-12:00、下午 14:00-18:00 安排主要活动，晚上安排美食
- 家庭出游节奏放慢，每天 3 个活动即可；独自/情侣游可以紧凑些（4 个）"""


async def route_agent_node(state: dict) -> dict:
    """路线详情节点 — 基于战略框架选择具体景点和排时间。

    输入：state["route_framework"], state["origin"], state["days"], state["crowd_type"]
    输出 → state["route_detail"]
    """
    llm = get_llm(
        temperature=0.5,
        streaming=False,
        request_timeout=120,
        max_tokens=4096,
        model_kwargs={"response_format": {"type": "json_object"}},
        reasoning_level="high",
    )

    framework = state.get("route_framework", {})
    if not framework:
        return {"route_detail": _fallback_route(state), "error": "route_framework 为空"}

    prompt = ROUTE_AGENT_PROMPT.format(
        route_framework=json.dumps(framework, ensure_ascii=False),
        origin=state.get("origin", ""),
        days=state.get("days", 3),
        crowd_type={"solo": "独自旅行", "couple": "情侣出游",
                     "family": "家庭出游", "friends": "朋友结伴"}.get(
                         state.get("crowd_type", "solo"), "自由行"),
    )

    try:
        response = await asyncio.wait_for(llm.ainvoke(prompt), timeout=120)
        content = response.content if hasattr(response, "content") else str(response)
        raw = str(content)
        cleaned = clean_json(raw)
        if cleaned:
            route_detail = json.loads(cleaned)
        else:
            raise ValueError("JSON extraction returned empty")
    except Exception as e:
        print(f"[RouteAgent] LLM 调用失败: {e}")
        route_detail = _fallback_route(state)

    return {"route_detail": route_detail}


def _fallback_route(state: dict) -> dict:
    """降级路线（当 LLM 不可用时）。"""
    days = state.get("days", 3)
    origin = state.get("origin", "")
    return {
        "transport": {
            "to": {"type": "高铁", "from": origin, "to": "潮汕站", "duration": "约2h", "cost": "¥150/人"},
            "return": {"type": "高铁", "from": "潮汕站", "to": origin, "duration": "约2h", "cost": "¥150/人"},
        },
        "days": [
            {
                "day": d + 1,
                "title": f"第{d+1}天 · 潮汕文化探索",
                "activities": [
                    {"time": "09:00", "name": "小公园骑楼群", "type": "scenery",
                     "lat": 23.357, "lng": 116.672, "description": "漫步百年商埠",
                     "duration": "2h", "reason": "标志性景点"},
                    {"time": "12:00", "name": "品尝牛肉火锅", "type": "food",
                     "lat": 23.358, "lng": 116.678, "description": "潮汕必吃美食",
                     "duration": "1.5h", "reason": "潮汕美食代表"},
                    {"time": "14:30", "name": "牌坊街", "type": "culture",
                     "lat": 23.665, "lng": 116.643, "description": "古城核心文化街",
                     "duration": "2h", "reason": "非遗文化集中地"},
                ],
            }
            for d in range(days)
        ],
    }
