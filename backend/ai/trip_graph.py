"""
TripGraph — LangGraph StateGraph 多 Agent 行程规划。

5 个节点（food_agent 和 hotel_agent 并行执行）：
    orchestrator_plan → route_agent → [food_agent ‖ hotel_agent] → orchestrator_merge → END

每个节点只追加写入自己的字段，不修改前序 Agent 输出。
外循环（trip_agent.py）对 A/B/C 三套方案分别跑一次管道。
"""
from typing import TypedDict

from langgraph.graph import StateGraph, END


# ═══════════════════════════════════════════
# TripState — 所有 Agent 间共享的数据模型
# ═══════════════════════════════════════════

class TripState(TypedDict):
    """多 Agent 行程规划的共享状态。

    各 Agent 只写入自己的输出字段，前序输出仅供读取。
    """

    # ── 输入参数（外循环注入，只读）──
    origin: str                     # 出发地，如 "深圳"
    days: int                       # 行程天数，如 3
    crowd_type: str                 # 出行人群：solo/couple/family/friends
    interests: list[str]            # 兴趣偏好，如 ["美食","非遗"]
    budget: str                     # 预算档位：low/mid/high
    theme: str                      # 方案主题，如 "美食之旅"
    plan_id: str                    # 方案 ID：A/B/C

    # ── orchestrator_plan 输出 ──
    route_framework: dict | None
    # {
    #   "city_flow": "深圳→汕头(2天)→潮州(1天)",
    #   "day_themes": [
    #     {"day":1, "theme":"抵达汕头，初探老城", "area":"汕头老城区"},
    #     ...
    #   ],
    #   "food_constraints": {"prefer_types":["牛肉火锅","海鲜"], "max_per_meal":80},
    #   "hotel_constraints": {"areas":["汕头老城"], "stars_min":3, "budget_night":300}
    # }

    # ── route_agent 输出 ──
    route_detail: dict | None
    # {
    #   "transport": {"to":{...}, "return":{...}},
    #   "days": [
    #     {"day":1, "title":"...", "activities":[
    #       {"time":"09:00","name":"...","type":"scenery","lat":...,"lng":...,
    #        "description":"...","duration":"2h","reason":"..."}
    #     ]}
    #   ]
    # }

    # ── food_agent 输出 ──
    food_recommendations: dict | None
    # {
    #   "recommendations": [
    #     {"day":1, "meal":"lunch", "foods":[
    #       {"food_id":5,"name":"八合里牛肉火锅","lat":...,"lng":...,
    #        "price":"¥80/人","reason":"...","tags":[...]}
    #     ]}
    #   ],
    #   "foods_summary": "本次行程共推荐 9 家餐厅，涵盖..."
    # }

    # ── hotel_agent 输出 ──
    hotel_recommendations: dict | None
    # {
    #   "hotels": [
    #     {"name":"...","stars":4,"price":350,"level":"comfort",
    #      "lat":...,"lng":...,"reason":"..."},
    #     ... (3档各1家)
    #   ]
    # }

    # ── orchestrator_merge 输出 ──
    merged_plan: dict | None       # 完整 plan JSON（兼容现有 TripCard 格式）
    error: str | None              # 任意节点可设置，触发前端降级处理


# ═══════════════════════════════════════════
# 图编译
# ═══════════════════════════════════════════

def create_trip_graph():
    """创建并编译 LangGraph StateGraph。

    拓扑（food_agent 和 hotel_agent 并行执行以加速）：
        orchestrator_plan → route_agent → food_agent ┐
                                          ├→ orchestrator_merge → END
                                     hotel_agent ──┘

    节点定义在各 agent 模块中：
        - agents.orchestrator: orchestrator_plan_node / orchestrator_merge_node
        - agents.route_agent: route_agent_node
        - agents.food_agent: food_agent_node
        - agents.hotel_agent: hotel_agent_node
    """
    from ai.agents.orchestrator import orchestrator_plan_node, orchestrator_merge_node
    from ai.agents.route_agent import route_agent_node
    from ai.agents.food_agent import food_agent_node
    from ai.agents.hotel_agent import hotel_agent_node

    graph = StateGraph(TripState)

    # 注册 5 个节点
    graph.add_node("orchestrator_plan", orchestrator_plan_node)
    graph.add_node("route_agent", route_agent_node)
    graph.add_node("food_agent", food_agent_node)
    graph.add_node("hotel_agent", hotel_agent_node)
    graph.add_node("orchestrator_merge", orchestrator_merge_node)

    # 并行拓扑：route_agent → food_agent + hotel_agent（并行）→ orchestrator_merge
    graph.set_entry_point("orchestrator_plan")
    graph.add_edge("orchestrator_plan", "route_agent")
    graph.add_edge("route_agent", "food_agent")
    graph.add_edge("route_agent", "hotel_agent")
    graph.add_edge("food_agent", "orchestrator_merge")
    graph.add_edge("hotel_agent", "orchestrator_merge")
    graph.add_edge("orchestrator_merge", END)

    return graph.compile()


# ═══════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════

_trip_graph_app = None


def get_trip_graph():
    """获取编译后的 TripGraph 单例（延迟初始化）。"""
    global _trip_graph_app
    if _trip_graph_app is None:
        _trip_graph_app = create_trip_graph()
    return _trip_graph_app
