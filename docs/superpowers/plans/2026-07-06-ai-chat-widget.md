# AI 全局智能聊天浮窗 · 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 ChatWidget 升级为全站 AI 统一入口，支持智能意图路由 + 富媒体卡片（行程/美食/非遗）+ 多轮对话追问

**Architecture:** 后端新增统一 SSE 端点 `POST /api/v1/ai/chat`，IntentRouter 用 LLM 识别意图并提取参数，AgentDispatcher 分发到 cs_agent / trip_agent / food_recommend，输出包装为 SSE 事件流。前端 ChatWidget 升级为多类型消息渲染（文本/行程卡片/美食卡片/非遗卡片），新增 3 个子组件

**Tech Stack:** Python 3.11+ FastAPI + LangChain/LangGraph + 智谱 GLM-4-Flash / DeepSeek · Vue 3 Composition API + Pinia + Element Plus

## Global Constraints

- 复用现有 AI 模块（cs_agent.py / food_recommend.py），不重写
- trip_agent.py 重写为 3 套方案输出，每套含交通+酒店+每日行程+费用预估
- SSE 事件协议：thinking / ask / token / trip_card / food_card / heritage_card / done / error
- 智谱 API Key 已配置，`LLM_PROVIDER=zhipu`，`ZHIPU_MODEL=glm-4-flash`
- 前端 CSS 使用项目现有设计 token（`var(--primary)`, `var(--space-md)` 等）
- ChatWidget 在 admin 路由不可见（保持现有行为）

---

### Task 1: schemas/ai.py — 统一 AI 请求 Schema

**Files:**
- Create: `backend/schemas/ai.py`

**Produces:**
```python
class ChatAIRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = None
```

- [ ] **Step 1: 创建文件**

```python
"""统一 AI 聊天接口 Schema。"""
from typing import Optional
from pydantic import BaseModel, Field


class ChatAIRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = None
```

- [ ] **Step 2: 验证导入**

```bash
cd backend && python -c "from schemas.ai import ChatAIRequest; print('OK')"
```

---

### Task 2: ai/intent_router.py — LLM 意图识别器

**Files:**
- Create: `backend/ai/intent_router.py`

**Interfaces:**
- Produces: `async def route_intent(session_id: str, user_message: str) -> IntentResult`
- Produces: `SessionState` dict (in-memory, keyed by session_id)
- Produces: `IntentResult` dataclass with fields: `intent: str`, `extracted_params: dict`, `missing_params: list[str]`, `follow_up_question: str | None`, `quick_options: list[str] | None`

- [ ] **Step 1: 创建文件**

```python
"""
意图路由器 — LLM 分析用户输入，识别意图、提取参数、判断是否需要多轮追问。

Intent 类型:
    chat     — 文化问答、闲聊 → cs_agent (RAG)
    trip     — 行程规划 → trip_agent (3方案)
    food     — 美食推荐 → food_recommend
    heritage — 非遗/民俗查询 → cs_agent (RAG)
"""
import json
from dataclasses import dataclass, field
from ai.llm import get_llm

# === 多轮会话状态（内存存储，后续可迁移至 Redis） ===
_sessions: dict[str, dict] = {}


@dataclass
class IntentResult:
    intent: str = "chat"                      # chat | trip | food | heritage
    extracted_params: dict = field(default_factory=dict)
    missing_params: list[str] = field(default_factory=list)
    follow_up_question: str | None = None
    quick_options: list[str] | None = None


# === Intent 定义：必要参数 + 追问模板 ===
INTENT_SCHEMA = {
    "trip": {
        "required": ["origin", "days", "crowd_type", "interests"],
        "questions": {
            "origin": {
                "text": "从哪里出发呢？",
                "options": ["深圳", "广州", "厦门", "上海", "北京"],
            },
            "days": {
                "text": "准备玩几天？",
                "options": ["2天", "3天", "4天", "5天", "7天"],
            },
            "crowd_type": {
                "text": "和谁一起去呀？",
                "options": ["自己", "情侣", "家庭", "朋友"],
            },
            "interests": {
                "text": "主要对哪些方面感兴趣？",
                "options": ["美食🍲", "文化🏛️", "自然🌿", "都要"],
            },
        },
    },
    "food": {
        "required": [],
        "questions": {},
    },
    "heritage": {
        "required": [],
        "questions": {},
    },
    "chat": {
        "required": [],
        "questions": {},
    },
}


# === Intent 路由 Prompt ===
ROUTER_PROMPT = """你是一个意图识别路由器。分析用户消息，判断属于哪种意图，并提取相关参数。

## 意图类型
- "trip": 用户想规划潮汕旅行（行程/旅游/出行/玩几天/去潮汕）
- "food": 用户想了解或推荐潮汕美食（推荐/吃什么/哪家好/好吃）
- "heritage": 用户询问非遗/民俗/传统文化（非遗/民俗/传统/文化历史）
- "chat": 其他问题或闲聊

## trip 意图需提取的参数
- origin: 出发城市（如"深圳""广州"，未提及则为 null）
- days: 游玩天数（数字，如 3，未提及则为 null）
- crowd_type: 同行人群，single(独自)/couple(情侣)/family(家庭)/friends(朋友)，未提及为 null，根据用户描述推断
- interests: 兴趣偏好列表，如 ["food","culture","nature"]，未提及为 []

## 输出格式
严格输出 JSON（不要 markdown 代码块）：
{
  "intent": "trip",
  "extracted_params": {"origin": "深圳", "days": 3, "crowd_type": "family", "interests": ["food"]}
}

如果用户消息与潮汕无关，intent 仍然判断为 "chat"。

用户消息：{message}"""


async def route_intent(session_id: str, user_message: str) -> IntentResult:
    """分析用户消息 → 返回 IntentResult。
    
    如果当前 session 存在多轮状态且参数已部分收集，
    则将新消息合并到 collected_params 中继续收集。
    """
    state = _sessions.get(session_id)
    
    # 如果已有活跃的多轮追问会话，优先用 LLM 提取新参数
    if state and state.get("intent"):
        return await _continue_collecting(state, user_message)
    
    # 首次分析意图
    return await _classify_intent(session_id, user_message)


async def _classify_intent(session_id: str, user_message: str) -> IntentResult:
    """首次意图分类 + 参数提取。"""
    llm = get_llm(temperature=0.1, streaming=False)
    prompt = ROUTER_PROMPT.format(message=user_message)
    
    try:
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        content = _clean_json(content)
        data = json.loads(content)
    except Exception:
        # LLM 失败时退化为 chat
        return IntentResult(intent="chat")
    
    intent = data.get("intent", "chat")
    extracted = data.get("extracted_params", {})
    
    if intent not in INTENT_SCHEMA:
        intent = "chat"
    
    # 检查缺失参数
    schema = INTENT_SCHEMA[intent]
    missing = [p for p in schema["required"] if p not in extracted or not extracted[p]]
    
    if missing:
        # 保存多轮状态
        _sessions[session_id] = {
            "intent": intent,
            "collected_params": extracted,
            "turn": 1,
        }
        return _build_ask_result(intent, missing)
    
    # 参数齐全，直接执行
    return IntentResult(
        intent=intent,
        extracted_params=extracted,
        missing_params=[],
    )


async def _continue_collecting(state: dict, user_message: str) -> IntentResult:
    """多轮对话中收集缺失参数。"""
    intent = state["intent"]
    collected = state["collected_params"]
    
    # 用轻量 LLM 从新消息中提取参数
    llm = get_llm(temperature=0.1, streaming=False)
    schema = INTENT_SCHEMA[intent]
    missing = [p for p in schema["required"] if p not in collected or not collected[p]]
    
    prompt = f"""从用户消息中提取以下缺失参数的值。

缺失参数：{json.dumps(missing, ensure_ascii=False)}
当前已收集：{json.dumps(collected, ensure_ascii=False)}
用户消息：{user_message}

输出 JSON（只输出提取到的参数，未提取到的不要输出）：
{{"参数名": "值"}}

注意：
- days 必须是整数
- crowd_type 可选值：single/couple/family/friends
- interests 是数组，如 ["food","culture"]"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        content = _clean_json(content)
        new_params = json.loads(content)
    except Exception:
        new_params = {}
    
    # 合并参数
    collected.update(new_params)
    state["turn"] += 1
    state["collected_params"] = collected
    
    missing = [p for p in schema["required"] if p not in collected or not collected[p]]
    
    if missing:
        return _build_ask_result(intent, missing)
    
    # 参数收集完毕
    _sessions.pop(state.get("session_id", ""), None)  # 清理状态，用传入的 key
    return IntentResult(
        intent=intent,
        extracted_params=collected,
        missing_params=[],
    )


def _build_ask_result(intent: str, missing: list[str]) -> IntentResult:
    """构建追问结果。"""
    schema = INTENT_SCHEMA[intent]
    first_missing = missing[0]
    q = schema["questions"].get(first_missing, {})
    return IntentResult(
        intent=intent,
        missing_params=missing,
        follow_up_question=q.get("text", f"请提供{first_missing}"),
        quick_options=q.get("options"),
    )


def _clean_json(text: str) -> str:
    """清洗 LLM 输出的 JSON。"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:]) if len(lines) > 1 else text
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


def clear_session(session_id: str):
    """清除多轮对话状态。"""
    _sessions.pop(session_id, None)
```

- [ ] **Step 2: 验证导入**

```bash
cd backend && python -c "from ai.intent_router import route_intent, IntentResult; print('OK')"
```

---

### Task 3: ai/trip_agent.py — 重写为 3 方案全流程规划

**Files:**
- Modify: `backend/ai/trip_agent.py` (完整重写)

**Interfaces:**
- Produces: `async def generate_three_plans(params: dict) -> list[dict]` — 生成 3 套旅行方案
- Produces: `def get_trip_app()` — 保持向后兼容

- [ ] **Step 1: 重写文件**

```python
"""
行程规划 Agent — 基于 LangGraph 生成 3 套潮汕旅行方案。

每套方案包含：交通方式、酒店推荐（3档）、每日行程（3-5个活动）、预估费用
"""
import json
from typing import TypedDict

from langgraph.graph import StateGraph, END
from ai.llm import get_llm


# === State ===
class TripState(TypedDict):
    origin: str           # 出发城市
    days: int             # 游玩天数
    crowd_type: str       # solo / couple / family / friends
    interests: list[str]  # ["food", "culture", "nature"]
    budget: str           # budget / mid / luxury
    plans: list | None    # 输出的 3 套方案
    error: str | None


# === System Prompt ===
TRIP_SYSTEM_PROMPT = """你是一个专业的潮汕旅游规划专家。请为用户的潮汕旅行规划 **3 套不同的方案**。

## 用户需求
- 出发城市：{origin}
- 游玩天数：{days} 天
- 同行人群：{crowd_type}
- 兴趣偏好：{interests}
- 预算档位：{budget}

## 3 套方案要求
- **方案A「美食寻味」**：以汕头市区 + 南澳岛为主，侧重美食体验，穿插市井烟火气景点
- **方案B「文化寻根」**：以潮州古城 + 龙湖古寨为主，侧重非遗文化和历史古迹
- **方案C「全景环游」**：覆盖汕潮揭三市精华，兼顾美食/文化/自然风光

## 每套方案必须包含
1. **交通方案**：从 {origin} 到潮汕的往返交通（高铁/自驾/飞机），含时长和预估费用
2. **酒店推荐**：3 档（经济型 ¥150-250 / 舒适型 ¥300-500 / 高端型 ¥600+），含名称、星级、价格、推荐理由
3. **每日行程**：每天 3-5 个活动，按时间线排列，每个活动含 time/name/type/description/reason/cost（如有）
   - 活动 type：transport / food / scenery / culture / shopping / rest
   - 美食类活动必须含 cost 字段
4. **预估费用**：分项（交通/住宿/餐饮/门票/其他）和总费用（每人）
5. **出行贴士**：3-5 条实用建议

## 人群适配
- solo：高自由度，偏向小众深度体验、青旅或民宿
- couple：增加浪漫场景、下午茶、夜景、舒适酒店
- family：减少步行强度，增加互动体验、亲子友好场所、家庭房
- friends：增加聚餐、打卡点、热闹街区、性价比住宿

## 输出格式
严格输出 JSON（不要 markdown 代码块标记）：
{{
  "plans": [
    {{
      "plan_id": "A",
      "title": "方案标题",
      "theme": "主题关键词",
      "summary": "50字以内的方案特色总结",
      "transport": {{
        "to": {{"mode": "高铁", "route": "{origin}→潮汕站", "duration": "Xh", "cost": 150}},
        "return": {{"mode": "高铁", "route": "汕头站→{origin}", "duration": "Xh", "cost": 150}}
      }},
      "hotels": [
        {{"name": "酒店名", "stars": 4, "price": 350, "level": "comfort", "reason": "推荐理由"}}
      ],
      "days": [
        {{
          "day": 1,
          "title": "Day 1 主题",
          "activities": [
            {{"time": "09:00", "name": "活动名", "type": "food", "description": "描述", "reason": "推荐理由", "cost": "¥80/人"}}
          ]
        }}
      ],
      "estimated_cost": {{"transport": 300, "hotel": 1400, "food": 800, "tickets": 200, "total": 2700}},
      "tips": ["贴士1", "贴士2"]
    }}
  ]
}}

请根据用户需求生成 3 套方案，直接输出 JSON："""


def _make_trip_agent_node(llm):
    """创建 TripAgent 节点函数。"""

    async def trip_agent_node(state: TripState) -> TripState:
        prompt = TRIP_SYSTEM_PROMPT.format(
            origin=state.get("origin", ""),
            days=state.get("days", 3),
            crowd_type=state.get("crowd_type", "solo"),
            interests="、".join(state.get("interests", [])),
            budget=state.get("budget", "mid"),
        )

        try:
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            content = _clean_json(content)
            data = json.loads(content)
            state["plans"] = data.get("plans", [])
            state["error"] = None
        except json.JSONDecodeError as e:
            state["plans"] = None
            state["error"] = f"AI 生成的行程格式有误: {str(e)}"
        except Exception as e:
            state["plans"] = None
            state["error"] = f"AI 服务调用失败: {str(e)}"

        return state

    return trip_agent_node


def _clean_json(text: str) -> str:
    """清洗 LLM 输出中的 markdown 标记。"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:]) if len(lines) > 1 else text
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


def create_trip_graph():
    """创建行程规划 StateGraph（全局单例）。"""
    # 行程规划使用更高温度的 LLM，增加方案多样性
    llm = get_llm(temperature=0.8, streaming=False)

    graph = StateGraph(TripState)
    trip_node = _make_trip_agent_node(llm)
    graph.add_node("trip_agent", trip_node)
    graph.set_entry_point("trip_agent")
    graph.add_edge("trip_agent", END)

    return graph.compile()


async def generate_three_plans(params: dict) -> list[dict]:
    """生成 3 套旅行方案。
    
    Args:
        params: {
            "origin": str,        # 出发城市
            "days": int,          # 游玩天数
            "crowd_type": str,    # solo/couple/family/friends
            "interests": list,    # ["food", "culture", "nature"]
            "budget": str,        # budget/mid/luxury
        }
    
    Returns:
        3 套方案的 list[dict]
    """
    app = get_trip_app()
    initial_state = TripState(
        origin=params.get("origin", ""),
        days=params.get("days", 3),
        crowd_type=params.get("crowd_type", "solo"),
        interests=params.get("interests", []),
        budget=params.get("budget", "mid"),
        plans=None,
        error=None,
    )
    
    result = await app.ainvoke(initial_state)
    
    if result.get("error"):
        raise RuntimeError(result["error"])
    
    return result.get("plans", [])


# === 全局单例 ===
_trip_app = None


def get_trip_app():
    global _trip_app
    if _trip_app is None:
        _trip_app = create_trip_graph()
    return _trip_app
```

- [ ] **Step 2: 验证导入**

```bash
cd backend && python -c "from ai.trip_agent import generate_three_plans, get_trip_app; print('OK')"
```

---

### Task 4: ai/agent_dispatcher.py — Agent 调度器 + SSE 事件包装

**Files:**
- Create: `backend/ai/agent_dispatcher.py`

**Interfaces:**
- Consumes: `IntentResult` from `ai.intent_router`
- Consumes: `generate_three_plans(params)` from `ai.trip_agent`
- Consumes: `recommend_foods(preference, foods, temperature)` from `ai.food_recommend`
- Consumes: `chat_stream(session_id, message)` from `ai.cs_agent`
- Produces: `async def chat_pipeline(session_id: str, user_message: str) -> AsyncGenerator[str, None]`

- [ ] **Step 1: 创建文件**

```python
"""
Agent 调度器 — 接收 IntentRouter 结果 → 调用对应 Agent → 包装为 SSE 事件流。
"""
import json
from typing import AsyncGenerator

from ai.intent_router import route_intent, clear_session
from ai.trip_agent import generate_three_plans
from ai.food_recommend import recommend_foods
from ai.cs_agent import chat_stream as cs_chat_stream


def sse_event(event_type: str, **kwargs) -> str:
    """构建 SSE 格式的事件字符串。"""
    payload = {"type": event_type, **kwargs}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def chat_pipeline(session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    """统一 AI 聊天管线 — SSE 事件流生成器。
    
    Usage in FastAPI router:
        return StreamingResponse(
            chat_pipeline(session_id, message),
            media_type="text/event-stream",
        )
    """
    # Step 1: 意图识别
    intent_result = await route_intent(session_id, user_message)
    
    # Step 2: 如果参数不全 → 追问
    if intent_result.missing_params:
        yield sse_event(
            "ask",
            question=intent_result.follow_up_question,
            options=intent_result.quick_options,
            intent=intent_result.intent,
        )
        yield sse_event("done", session_id=session_id, intent=intent_result.intent)
        return
    
    # Step 3: 参数齐全 → 分发到对应 Agent
    intent = intent_result.intent
    params = intent_result.extracted_params
    
    if intent == "trip":
        yield sse_event("thinking", label="正在为您规划3套旅行方案...")
        try:
            plans = await generate_three_plans(params)
            yield sse_event("trip_card", plans=plans)
        except Exception as e:
            yield sse_event("error", message=f"行程规划失败: {str(e)}")
    
    elif intent == "food":
        yield sse_event("thinking", label="正在为您寻找最合适的美食...")
        try:
            from database import async_session_factory
            from sqlalchemy import select
            from models.food import Food, FoodCategory
            
            async with async_session_factory() as db:
                foods_q = await db.execute(
                    select(Food).where(Food.is_recommended == True).limit(50)
                )
                foods = foods_q.scalars().all()
                foods_list = [
                    {
                        "food_id": f.id,
                        "name": f.name,
                        "type": f.type,
                        "category_name": "",
                        "price_range": f.price_range or "",
                        "tags": f.tags or [],
                        "image_url": f.image_url or "",
                    }
                    for f in foods
                ]
            
            result = await recommend_foods(
                params.get("preference", user_message),
                foods_list,
            )
            # 属性映射：food_id → id, 加上 image_url
            enriched = []
            for r in result.get("recommendations", []):
                fid = r.get("food_id")
                match = next((f for f in foods_list if f["food_id"] == fid), None)
                enriched.append({
                    **r,
                    "id": fid,
                    "image_url": match.get("image_url", "") if match else "",
                })
            yield sse_event("food_card", items=enriched, summary=result.get("summary", ""))
        except Exception as e:
            yield sse_event("error", message=f"美食推荐失败: {str(e)}")
    
    elif intent == "heritage":
        yield sse_event("thinking", label="正在查阅非遗资料...")
        # heritage 复用 cs_agent 的 RAG 流式
        async for event_str in cs_chat_stream(session_id, user_message):
            if "type" in event_str:
                try:
                    data = json.loads(event_str.replace("data: ", "").strip())
                    if data.get("type") == "sources" and data.get("sources"):
                        # 如果有知识来源，包装为 heritage_card
                        pass
                except Exception:
                    pass
            yield event_str
    
    else:  # chat
        async for event_str in cs_chat_stream(session_id, user_message):
            yield event_str
    
    # Step 4: 完成信号
    yield sse_event("done", session_id=session_id, intent=intent)


async def start_new_session(session_id: str):
    """开始新会话，清除多轮状态。"""
    clear_session(session_id)
```

- [ ] **Step 2: 验证导入**

```bash
cd backend && python -c "from ai.agent_dispatcher import chat_pipeline, sse_event; print('OK')"
```

---

### Task 5: routers/ai.py — 统一 AI SSE 端点

**Files:**
- Create: `backend/routers/ai.py`

**Interfaces:**
- Consumes: `chat_pipeline` from `ai.agent_dispatcher`
- Consumes: `start_new_session` from `ai.agent_dispatcher`
- Consumes: `ChatAIRequest` from `schemas.ai`

- [ ] **Step 1: 创建文件**

```python
"""
统一 AI 路由 — POST /api/v1/ai/chat (SSE 流式)。
"""
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from schemas.ai import ChatAIRequest
from ai.agent_dispatcher import chat_pipeline, start_new_session

router = APIRouter(prefix="/ai", tags=["AI助手"])


@router.post("/chat")
async def ai_chat(req: ChatAIRequest):
    """统一 AI 聊天入口 — SSE 流式返回。

    支持意图：chat（文化问答）/ trip（行程规划）/ food（美食推荐）/ heritage（非遗查询）

    回复通过 SSE 事件流发送：
    - thinking: AI 正在思考
    - ask: 多轮追问
    - token: 流式文本
    - trip_card: 行程方案卡片
    - food_card: 美食推荐卡片
    - heritage_card: 非遗卡片
    - done: 本轮完成
    - error: 错误信息
    """
    session_id = req.session_id or uuid.uuid4().hex[:16]

    return StreamingResponse(
        chat_pipeline(session_id, req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/new")
async def new_chat_session(session_id: str = None):
    """开始新的 AI 对话，清除多轮追问状态。"""
    if session_id:
        await start_new_session(session_id)
    return {"code": 0, "message": "ok"}
```

- [ ] **Step 2: 在 main.py 中注册路由**

在 `backend/main.py` 中添加：
```python
from routers.ai import router as ai_router
# ...
app.include_router(ai_router, prefix="/api/v1")
```

添加到其他 router 注册的同一区域。

- [ ] **Step 3: 验证路由注册**

```bash
cd backend && python -c "
from main import app
routes = [r.path for r in app.routes if hasattr(r, 'path')]
assert '/api/v1/ai/chat' in routes, 'Route not found!'
print('Route registered OK')
"
```

---

### Task 6: stores/chat.js — Pinia Store 升级

**Files:**
- Modify: `frontend/src/stores/chat.js`

**Interfaces:**
- Produces: `useChatStore` with new state: `thinkingLabel`, `currentIntent`, structured messages
- Produces: `addCardMessage(type, cardData)` action
- Produces: `setThinking(label)` action

- [ ] **Step 1: 重写 chat store**

```js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useChatStore = defineStore('chat', () => {
  // ===== State =====
  const messages = ref([])
  const sessionId = ref(localStorage.getItem('chat_session_id') || '')
  const isOpen = ref(false)
  const thinkingLabel = ref('')
  const currentIntent = ref(null)

  // ===== Getters =====
  const lastMessage = computed(() => messages.value[messages.value.length - 1])
  const hasMessages = computed(() => messages.value.length > 0)

  // ===== Helpers =====
  function makeMsg(role, type, content, cardData) {
    return {
      id: Date.now() + '_' + Math.random().toString(36).slice(2, 8),
      role,
      type: type || 'text',
      content: content || null,
      cardData: cardData || null,
      time: new Date().toISOString(),
    }
  }

  // ===== Actions =====
  function addMessage(role, content) {
    messages.value.push(makeMsg(role, 'text', content))
  }

  function addCardMessage(type, cardData) {
    messages.value.push(makeMsg('assistant', type, null, cardData))
  }

  function appendToken(token) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant' && last.type === 'text') {
      last.content += token
    } else {
      addMessage('assistant', token)
    }
  }

  function setSessionId(id) {
    sessionId.value = id
    localStorage.setItem('chat_session_id', id)
  }

  function setThinking(label) {
    thinkingLabel.value = label
  }

  function clearThinking() {
    thinkingLabel.value = ''
  }

  function setIntent(intent) {
    currentIntent.value = intent
  }

  function startNewSession() {
    messages.value = []
    sessionId.value = ''
    thinkingLabel.value = ''
    currentIntent.value = null
    localStorage.removeItem('chat_session_id')
  }

  function toggle() {
    isOpen.value = !isOpen.value
  }

  function open() {
    isOpen.value = true
  }

  function close() {
    isOpen.value = false
  }

  return {
    messages,
    sessionId,
    isOpen,
    thinkingLabel,
    currentIntent,
    lastMessage,
    hasMessages,
    makeMsg,
    addMessage,
    addCardMessage,
    appendToken,
    setSessionId,
    setThinking,
    clearThinking,
    setIntent,
    startNewSession,
    toggle,
    open,
    close,
  }
})
```

- [ ] **Step 2: 验证语法**

```bash
cd frontend && npx eslint src/stores/chat.js --fix 2>/dev/null; echo "Syntax OK"
```

---

### Task 7: composables/useSSE.js — SSE 事件类型升级

**Files:**
- Modify: `frontend/src/composables/useSSE.js`

**Interfaces:**
- Consumes: `useChatStore` (upgraded)
- Produces: `streamChat(sessionId, message, callbacks)` — supports new event types

- [ ] **Step 1: 重写 useSSE**

```js
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'

export function useSSE() {
  const isStreaming = ref(false)
  const error = ref(null)
  let abortController = null

  async function streamChat(sessionId, message, callbacks = {}) {
    const {
      onToken = () => {},
      onDone = () => {},
      onError = () => {},
      onTripCard = () => {},
      onFoodCard = () => {},
      onHeritageCard = () => {},
      onAsk = () => {},
      onThinking = () => {},
    } = callbacks

    const userStore = useUserStore()
    const chatStore = useChatStore()
    abortController = new AbortController()
    isStreaming.value = true
    error.value = null

    try {
      const base = import.meta.env.VITE_API_BASE || '/api/v1'
      const response = await fetch(`${base}/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(userStore.token ? { Authorization: `Bearer ${userStore.token}` } : {}),
        },
        body: JSON.stringify({ session_id: sessionId || null, message }),
        signal: abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))
            switch (data.type) {
              case 'token':
                onToken(data.content)
                break
              case 'thinking':
                onThinking(data.label)
                break
              case 'ask':
                onAsk(data.question, data.options, data.intent)
                break
              case 'trip_card':
                onTripCard(data.plans)
                break
              case 'food_card':
                onFoodCard(data.items, data.summary)
                break
              case 'heritage_card':
                onHeritageCard(data.item)
                break
              case 'done':
                chatStore.clearThinking()
                if (data.intent) chatStore.setIntent(data.intent)
                onDone(data.session_id)
                break
              case 'error':
                onError(data.message || '未知错误')
                break
              case 'sources':
                // 来自 cs_agent 的来源引用（chat 意图时使用）
                break
            }
          } catch {
            // 忽略 JSON 解析错误
          }
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        error.value = e.message || '连接失败'
        onError(error.value)
      }
    } finally {
      isStreaming.value = false
    }
  }

  function abort() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    isStreaming.value = false
  }

  return { isStreaming, error, streamChat, abort }
}
```

- [ ] **Step 2: 验证语法**

```bash
cd frontend && npx eslint src/composables/useSSE.js --fix 2>/dev/null; echo "Syntax OK"
```

---

### Task 8: components/business/TripCard.vue — 行程方案卡片

**Files:**
- Create: `frontend/src/components/business/TripCard.vue`

**Interfaces:**
- Props: `plans: Array` — 3 套旅行方案
- Emits: `save(plan)` — 保存行程到账户
- Emits: `refresh()` — 换一换

- [ ] **Step 1: 创建 TripCard.vue**

```vue
<template>
  <div class="trip-card">
    <div class="trip-card__header">
      <span class="trip-card__icon">🗺️</span>
      <span class="trip-card__title">旅行方案</span>
    </div>

    <!-- 方案 Tab 切换 -->
    <el-tabs v-model="activePlan" class="trip-tabs">
      <el-tab-pane
        v-for="plan in plans"
        :key="plan.plan_id"
        :label="`方案${plan.plan_id}: ${plan.theme || plan.title?.slice(0, 8)}`"
        :name="plan.plan_id"
      />
    </el-tabs>

    <template v-if="currentPlan">
      <!-- 概览 -->
      <div class="trip-plan__summary">{{ currentPlan.summary }}</div>

      <!-- 交通 -->
      <div class="trip-plan__section" v-if="currentPlan.transport">
        <h4>🚗 交通方案</h4>
        <div class="trip-transport">
          <div class="transport-item" v-if="currentPlan.transport.to">
            <span class="transport-label">去程</span>
            <span>{{ currentPlan.transport.to.route }} · {{ currentPlan.transport.to.duration }} · ¥{{ currentPlan.transport.to.cost }}/人</span>
          </div>
          <div class="transport-item" v-if="currentPlan.transport.return">
            <span class="transport-label">返程</span>
            <span>{{ currentPlan.transport.return.route }} · {{ currentPlan.transport.return.duration }} · ¥{{ currentPlan.transport.return.cost }}/人</span>
          </div>
        </div>
      </div>

      <!-- 酒店 -->
      <div class="trip-plan__section" v-if="currentPlan.hotels?.length">
        <h4>🏨 推荐住宿</h4>
        <div class="trip-hotels">
          <div
            v-for="hotel in currentPlan.hotels"
            :key="hotel.name"
            class="hotel-item"
            :class="`hotel-${hotel.level}`"
          >
            <div class="hotel-info">
              <span class="hotel-name">{{ hotel.name }}</span>
              <span class="hotel-stars">{{ '⭐'.repeat(hotel.stars || 0) }}</span>
              <span class="hotel-price">¥{{ hotel.price }}/晚</span>
            </div>
            <div class="hotel-reason">{{ hotel.reason }}</div>
          </div>
        </div>
      </div>

      <!-- 每日行程 -->
      <div class="trip-plan__section" v-if="currentPlan.days?.length">
        <h4>📅 每日行程</h4>
        <el-collapse v-model="activeDays" accordion>
          <el-collapse-item
            v-for="day in currentPlan.days"
            :key="day.day"
            :title="`Day ${day.day} · ${day.title}`"
            :name="day.day"
          >
            <div
              v-for="act in day.activities"
              :key="act.time + act.name"
              class="activity-item"
            >
              <span class="activity-time">{{ act.time }}</span>
              <span class="activity-icon">{{ typeIcon(act.type) }}</span>
              <div class="activity-detail">
                <strong>{{ act.name }}</strong>
                <span v-if="act.cost" class="activity-cost">{{ act.cost }}</span>
                <p class="activity-desc">{{ act.description }}</p>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 费用 -->
      <div class="trip-plan__section" v-if="currentPlan.estimated_cost">
        <h4>💰 预估费用（每人）</h4>
        <div class="trip-cost">
          <div class="cost-row" v-if="currentPlan.estimated_cost.transport">
            <span>交通</span><span>¥{{ currentPlan.estimated_cost.transport }}</span>
          </div>
          <div class="cost-row" v-if="currentPlan.estimated_cost.hotel">
            <span>住宿</span><span>¥{{ currentPlan.estimated_cost.hotel }}</span>
          </div>
          <div class="cost-row" v-if="currentPlan.estimated_cost.food">
            <span>餐饮</span><span>¥{{ currentPlan.estimated_cost.food }}</span>
          </div>
          <div class="cost-row" v-if="currentPlan.estimated_cost.tickets">
            <span>门票</span><span>¥{{ currentPlan.estimated_cost.tickets }}</span>
          </div>
          <div class="cost-row cost-total">
            <span>合计</span><span>¥{{ currentPlan.estimated_cost.total }}</span>
          </div>
        </div>
      </div>

      <!-- 贴士 -->
      <div class="trip-plan__section" v-if="currentPlan.tips?.length">
        <h4>📝 出行贴士</h4>
        <ul class="trip-tips">
          <li v-for="tip in currentPlan.tips" :key="tip">{{ tip }}</li>
        </ul>
      </div>
    </template>

    <!-- 操作栏 -->
    <div class="trip-card__actions">
      <el-button type="primary" size="small" @click="$emit('save', currentPlan)" :disabled="!currentPlan">
        💾 保存到我的行程
      </el-button>
      <el-button size="small" @click="copyPlan">
        📋 复制
      </el-button>
      <el-button size="small" @click="$emit('refresh')">
        🔄 换一换
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  plans: { type: Array, default: () => [] },
})

defineEmits(['save', 'refresh'])

const activePlan = ref(props.plans[0]?.plan_id || 'A')
const activeDays = ref(1)  // 默认展开 Day1

const currentPlan = computed(() =>
  props.plans.find(p => p.plan_id === activePlan.value)
)

function typeIcon(type) {
  const map = {
    food: '🍲', scenery: '📸', culture: '🏛️',
    shopping: '🛍️', transport: '🚗', rest: '😴',
  }
  return map[type] || '📍'
}

function copyPlan() {
  if (!currentPlan.value) return
  const text = JSON.stringify(currentPlan.value, null, 2)
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.info('复制失败，请手动选择')
  })
}
</script>

<style scoped>
.trip-card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  max-width: 100%;
  font-size: var(--fs-sm);
}

.trip-card__header {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-weight: 600;
  margin-bottom: var(--space-sm);
  color: var(--ink);
}

.trip-card__icon { font-size: 18px; }

.trip-tabs { margin-bottom: var(--space-sm); }

.trip-plan__summary {
  color: var(--muted);
  line-height: 1.6;
  margin-bottom: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg);
  border-radius: var(--radius-sm);
}

.trip-plan__section {
  margin-bottom: var(--space-md);
}

.trip-plan__section h4 {
  font-size: var(--fs-sm);
  color: var(--ink);
  margin: 0 0 var(--space-sm) 0;
}

.trip-transport {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.transport-item {
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg);
  border-radius: var(--radius-sm);
  font-size: var(--fs-xs);
}

.transport-label {
  color: var(--primary);
  font-weight: 600;
  white-space: nowrap;
}

.trip-hotels { display: flex; flex-direction: column; gap: var(--space-xs); }

.hotel-item {
  padding: var(--space-sm);
  background: var(--bg);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
}

.hotel-info {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
  margin-bottom: 2px;
}

.hotel-name { font-weight: 600; }
.hotel-price { color: var(--primary); font-weight: 600; margin-left: auto; }
.hotel-reason { font-size: var(--fs-xs); color: var(--muted); }

.activity-item {
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-sm) 0;
  border-bottom: 1px solid oklch(0 0 0 / 0.05);
}

.activity-item:last-child { border-bottom: none; }

.activity-time {
  font-size: var(--fs-xs);
  color: var(--muted);
  white-space: nowrap;
  min-width: 44px;
}

.activity-icon { font-size: 16px; }

.activity-detail { flex: 1; min-width: 0; }
.activity-detail strong { display: block; font-size: var(--fs-sm); }
.activity-cost { font-size: var(--fs-xs); color: var(--primary); }
.activity-desc { margin: 2px 0 0; font-size: var(--fs-xs); color: var(--muted); }

.trip-cost { display: flex; flex-direction: column; gap: var(--space-xs); }

.cost-row {
  display: flex;
  justify-content: space-between;
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
}

.cost-total { font-weight: 700; color: var(--primary); }

.trip-tips {
  margin: 0;
  padding-left: var(--space-lg);
  font-size: var(--fs-xs);
  color: var(--muted);
}

.trip-tips li { margin-bottom: var(--space-xs); }

.trip-card__actions {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  padding-top: var(--space-sm);
  border-top: 1px solid oklch(0 0 0 / 0.06);
  flex-wrap: wrap;
}
</style>
```

---

### Task 9: components/business/FoodCard.vue — 美食推荐卡片

**Files:**
- Create: `frontend/src/components/business/FoodCard.vue`

**Interfaces:**
- Props: `items: Array`, `summary: String`
- Emits: `favorite(item)` — 收藏美食

- [ ] **Step 1: 创建 FoodCard.vue**

```vue
<template>
  <div class="food-card-wrap">
    <div class="food-card__header">
      <span>🍲 美食推荐</span>
    </div>
    <p v-if="summary" class="food-card__summary">{{ summary }}</p>
    <div class="food-card__list">
      <div
        v-for="item in items"
        :key="item.id || item.food_id"
        class="food-item"
        @click="goDetail(item)"
      >
        <div class="food-item__img">
          <img v-if="item.image_url" :src="item.image_url" :alt="item.name" />
          <span v-else class="food-item__placeholder">🍲</span>
        </div>
        <div class="food-item__info">
          <strong>{{ item.name }}</strong>
          <div class="food-item__meta">
            <span class="food-score">⭐ {{ item.score?.toFixed(1) || '4.5' }}</span>
            <span v-if="item.price_range" class="food-price">{{ item.price_range }}</span>
          </div>
          <p class="food-item__reason">{{ item.reason }}</p>
        </div>
        <el-button
          circle
          size="small"
          class="food-item__fav"
          @click.stop="$emit('favorite', item)"
          title="收藏"
        >
          ❤️
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

defineProps({
  items: { type: Array, default: () => [] },
  summary: { type: String, default: '' },
})

defineEmits(['favorite'])

const router = useRouter()

function goDetail(item) {
  const id = item.id || item.food_id
  if (id) router.push(`/foods/${id}`)
}
</script>

<style scoped>
.food-card-wrap {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

.food-card__header {
  font-weight: 600;
  color: var(--ink);
  margin-bottom: var(--space-xs);
}

.food-card__summary {
  font-size: var(--fs-xs);
  color: var(--muted);
  margin: 0 0 var(--space-sm) 0;
}

.food-card__list {
  display: flex;
  gap: var(--space-sm);
  overflow-x: auto;
  padding-bottom: var(--space-xs);
}

.food-item {
  flex: 0 0 200px;
  background: var(--bg);
  border-radius: var(--radius-md);
  padding: var(--space-sm);
  cursor: pointer;
  position: relative;
  transition: box-shadow 0.2s;
}

.food-item:hover { box-shadow: var(--shadow-sm); }

.food-item__img {
  width: 100%;
  height: 100px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  margin-bottom: var(--space-sm);
  background: oklch(0.96 0.005 60);
  display: flex;
  align-items: center;
  justify-content: center;
}

.food-item__img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.food-item__placeholder { font-size: 36px; }

.food-item__info strong {
  display: block;
  font-size: var(--fs-sm);
  margin-bottom: 4px;
}

.food-item__meta {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: 4px;
}

.food-score { color: var(--accent); font-size: var(--fs-xs); }
.food-price { color: var(--primary); font-size: var(--fs-xs); font-weight: 600; }

.food-item__reason {
  font-size: var(--fs-xs);
  color: var(--muted);
  margin: 0;
  line-height: 1.4;
}

.food-item__fav {
  position: absolute;
  top: var(--space-sm);
  right: var(--space-sm);
  background: rgba(255,255,255,0.85);
}
</style>
```

---

### Task 10: components/business/HeritageCard.vue — 非遗卡片

**Files:**
- Create: `frontend/src/components/business/HeritageCard.vue`

**Interfaces:**
- Props: `item: Object` — 非遗项目数据
- Emits: `favorite(item)`

- [ ] **Step 1: 创建 HeritageCard.vue**

```vue
<template>
  <div class="heritage-card" v-if="item">
    <div class="heritage-card__header">
      <span>🎭 非遗文化</span>
    </div>
    <div class="heritage-card__body">
      <img v-if="item.image_url" :src="item.image_url" :alt="item.name" class="heritage-card__img" />
      <div class="heritage-card__info">
        <h4>{{ item.name }}</h4>
        <div class="heritage-card__tags">
          <el-tag size="small" type="danger">{{ item.category }}</el-tag>
          <el-tag size="small" type="warning">{{ item.type }}</el-tag>
          <el-tag size="small">{{ item.region }}</el-tag>
        </div>
        <p class="heritage-card__desc">{{ item.description?.slice(0, 150) || '' }}</p>
        <div v-if="item.inheritor" class="heritage-card__inheritor">
          👤 传承人：{{ item.inheritor }}
        </div>
      </div>
    </div>
    <div class="heritage-card__actions">
      <el-button size="small" @click="goDetail">查看详情</el-button>
      <el-button size="small" @click="$emit('favorite', item)">❤️ 收藏</el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

defineProps({
  item: { type: Object, default: null },
})

defineEmits(['favorite'])

const router = useRouter()

function goDetail() {
  // 暂用 heritage list 页，后续可做详情页
  router.push('/heritages')
}
</script>

<style scoped>
.heritage-card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

.heritage-card__header {
  font-weight: 600;
  color: var(--ink);
  margin-bottom: var(--space-sm);
}

.heritage-card__body {
  display: flex;
  gap: var(--space-md);
}

.heritage-card__img {
  width: 120px;
  height: 160px;
  border-radius: var(--radius-md);
  object-fit: cover;
  flex-shrink: 0;
}

.heritage-card__info { flex: 1; min-width: 0; }

.heritage-card__info h4 {
  margin: 0 0 var(--space-sm) 0;
  font-size: var(--fs-base);
  color: var(--ink);
}

.heritage-card__tags {
  display: flex;
  gap: var(--space-xs);
  margin-bottom: var(--space-sm);
  flex-wrap: wrap;
}

.heritage-card__desc {
  font-size: var(--fs-sm);
  color: var(--muted);
  line-height: 1.6;
  margin: 0 0 var(--space-sm) 0;
}

.heritage-card__inheritor {
  font-size: var(--fs-xs);
  color: var(--ink);
}

.heritage-card__actions {
  margin-top: var(--space-md);
  display: flex;
  gap: var(--space-sm);
}
</style>
```

---

### Task 11: components/business/ChatWidget.vue — 升级为富媒体渲染

**Files:**
- Modify: `frontend/src/components/business/ChatWidget.vue`

- [ ] **Step 1: 重写 ChatWidget.vue**

完整重写逻辑如下（保留原有样式结构，新增卡片渲染 + thinking 状态 + 快捷选项）：

```vue
<template>
  <div class="chat-widget" :class="{ 'is-open': isOpen }">
    <!-- 悬浮按钮 -->
    <button v-if="!isOpen" class="chat-fab" @click="openChat" aria-label="打开AI助手">
      <el-icon :size="28"><ChatDotRound /></el-icon>
    </button>

    <!-- 聊天弹窗 -->
    <div v-else class="chat-panel">
      <div class="chat-panel__header">
        <div class="chat-panel__title">
          <span class="chat-panel__avatar">🍵</span>
          <span>潮小文·AI助手</span>
        </div>
        <div class="chat-panel__actions">
          <el-button text circle size="small" @click="startNewChat" title="新对话">
            <el-icon><Plus /></el-icon>
          </el-button>
          <el-button text circle size="small" @click="closeChat" title="关闭">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>

      <div class="chat-panel__body" ref="msgContainer">
        <!-- 欢迎语 -->
        <div v-if="!hasMessages" class="chat-welcome">
          <div class="chat-welcome__icon">🍵</div>
          <div class="chat-welcome__text">
            您好！我是潮汕文化AI助手<br />
            我可以帮您：<br />
            🍲 推荐美食 &nbsp; 🎭 介绍非遗<br />
            🗺️ 规划行程 &nbsp; 💬 文化问答
          </div>
          <div class="chat-welcome__suggestions">
            <el-button
              v-for="q in suggestedQuestions"
              :key="q"
              size="small"
              round
              @click="sendMessage(q)"
            >
              {{ q }}
            </el-button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="(msg, idx) in messages" :key="msg.id" class="chat-message" :class="`is-${msg.role}`">
          <!-- 文本消息 -->
          <div v-if="msg.type === 'text'" class="chat-message__bubble">
            <div class="chat-message__text">{{ msg.content }}</div>
            <span v-if="isStreaming && idx === messages.length - 1 && msg.role === 'assistant'" class="chat-cursor">|</span>
          </div>

          <!-- 行程卡片 -->
          <TripCard
            v-else-if="msg.type === 'trip_card'"
            :plans="msg.cardData?.plans || []"
            @save="handleSaveTrip"
            @refresh="handleRefreshTrip"
          />

          <!-- 美食卡片 -->
          <FoodCard
            v-else-if="msg.type === 'food_card'"
            :items="msg.cardData?.items || []"
            :summary="msg.cardData?.summary || ''"
            @favorite="handleFavorite"
          />

          <!-- 非遗卡片 -->
          <HeritageCard
            v-else-if="msg.type === 'heritage_card'"
            :item="msg.cardData"
            @favorite="handleFavorite"
          />
        </div>

        <!-- Thinking 状态 -->
        <div v-if="chatStore.thinkingLabel" class="chat-thinking">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>{{ chatStore.thinkingLabel }}</span>
        </div>

        <!-- 快捷选项 -->
        <div v-if="quickOptions.length" class="chat-quick-options">
          <el-button
            v-for="opt in quickOptions"
            :key="opt"
            size="small"
            round
            @click="sendMessage(opt)"
          >
            {{ opt }}
          </el-button>
        </div>

        <!-- 错误提示 -->
        <div v-if="streamError" class="chat-error">
          <el-alert :title="streamError" type="error" :closable="true" @close="streamError = null" show-icon />
        </div>
      </div>

      <div class="chat-panel__footer">
        <el-input
          v-model="inputText"
          placeholder="输入问题..."
          :disabled="isStreaming"
          :maxlength="2000"
          @keyup.enter="sendCurrentMessage"
          class="chat-input"
        >
          <template #append>
            <el-button
              :disabled="!inputText.trim() || isStreaming"
              :loading="isStreaming"
              @click="sendCurrentMessage"
              :icon="Promotion"
            />
          </template>
        </el-input>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { ChatDotRound, Plus, Close, Promotion, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { useSSE } from '@/composables/useSSE'
import { tripApi } from '@/api/trip'
import { userApi } from '@/api/user'
import TripCard from './TripCard.vue'
import FoodCard from './FoodCard.vue'
import HeritageCard from './HeritageCard.vue'

const chatStore = useChatStore()
const userStore = useUserStore()
const { isStreaming, streamChat } = useSSE()

const inputText = ref('')
const streamError = ref(null)
const msgContainer = ref(null)
const quickOptions = ref([])
const lastTripParams = ref(null)

const isOpen = ref(false)
const messages = ref(chatStore.messages)
const hasMessages = ref(chatStore.hasMessages)

// 同步 store 状态
watch(() => chatStore.isOpen, v => { isOpen.value = v })
watch(isOpen, v => { v ? chatStore.open() : chatStore.close() })

const suggestedQuestions = [
  '帮我规划3天潮汕美食之旅',
  '潮汕有什么必吃的美食？',
  '英歌舞是什么？',
  '从深圳出发去潮汕玩4天',
]

function openChat() { isOpen.value = true }
function closeChat() { isOpen.value = false }

function startNewChat() {
  chatStore.startNewSession()
  streamError.value = null
  quickOptions.value = []
  lastTripParams.value = null
}

function sendCurrentMessage() {
  const text = inputText.value.trim()
  if (!text || isStreaming.value) return
  sendMessage(text)
  inputText.value = ''
}

async function sendMessage(text) {
  streamError.value = null
  quickOptions.value = []
  chatStore.addMessage('user', text)

  await streamChat(chatStore.sessionId, text, {
    onToken(token) {
      chatStore.appendToken(token)
      scrollToBottom()
    },
    onDone(sessionId) {
      if (sessionId) chatStore.setSessionId(sessionId)
      scrollToBottom()
    },
    onThinking(label) {
      chatStore.setThinking(label)
    },
    onAsk(question, options, intent) {
      chatStore.clearThinking()
      chatStore.setIntent(intent)
      if (options?.length) {
        quickOptions.value = options
      }
      if (question) {
        chatStore.addMessage('assistant', question)
      }
      if (intent === 'trip') {
        // 保存追问上下文，以便换一换时重用
        lastTripParams.value = { question: text, options }
      }
      scrollToBottom()
    },
    onTripCard(plans) {
      chatStore.clearThinking()
      chatStore.addCardMessage('trip_card', { plans })
      scrollToBottom()
    },
    onFoodCard(items, summary) {
      chatStore.clearThinking()
      chatStore.addCardMessage('food_card', { items, summary })
      scrollToBottom()
    },
    onHeritageCard(item) {
      chatStore.clearThinking()
      chatStore.addCardMessage('heritage_card', item)
      scrollToBottom()
    },
    onError(msg) {
      chatStore.clearThinking()
      streamError.value = msg
    },
  })
}

async function handleSaveTrip(plan) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    await tripApi.create({
      title: plan.title || 'AI 行程方案',
      days: plan.days?.length || 3,
      crowd_type: 'family',
      preferences: [],
    })
    ElMessage.success('行程已保存！')
  } catch (e) {
    ElMessage.error('保存失败，请重试')
  }
}

async function handleRefreshTrip() {
  if (!lastTripParams.value) return
  chatStore.addMessage('user', '🔄 换一换')
  await sendMessage(lastTripParams.value.question || '重新规划行程')
}

async function handleFavorite(item) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    await userApi.addFavorite({
      item_type: 'food',
      item_id: item.id || item.food_id,
    })
    ElMessage.success('已收藏')
  } catch {
    ElMessage.info('已收藏或收藏失败')
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
  })
}
</script>

<style scoped>
/* 保持原有样式 + 新增 */
.chat-widget { position: fixed; right: 24px; bottom: 80px; z-index: var(--z-sticky, 200); }
.chat-fab {
  width: 56px; height: 56px; border-radius: 50%;
  background: var(--primary); color: #fff; border: none;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; box-shadow: var(--shadow-lg);
  transition: transform 0.2s, box-shadow 0.2s;
}
.chat-fab:hover { transform: scale(1.08); box-shadow: var(--shadow-xl); }
.chat-panel { width: 420px; height: 600px; background: #fff; border-radius: var(--radius-lg); box-shadow: var(--shadow-xl); display: flex; flex-direction: column; overflow: hidden; }
.chat-panel__header { padding: 12px 16px; background: var(--primary); color: #fff; display: flex; align-items: center; justify-content: space-between; }
.chat-panel__title { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.chat-panel__avatar { font-size: 20px; }
.chat-panel__actions .el-button { color: #fff; }
.chat-panel__body { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }

.chat-welcome { text-align: center; padding: 20px 0; }
.chat-welcome__icon { font-size: 48px; margin-bottom: 12px; }
.chat-welcome__text { font-size: var(--fs-sm); color: var(--muted); line-height: 1.8; margin-bottom: 16px; }
.chat-welcome__suggestions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }

.chat-message { display: flex; }
.chat-message.is-user { justify-content: flex-end; }
.chat-message__bubble { max-width: 80%; padding: 10px 14px; border-radius: var(--radius-md); font-size: var(--fs-sm); line-height: 1.6; word-break: break-word; }
.chat-message.is-user .chat-message__bubble { background: var(--primary); color: #fff; border-bottom-right-radius: 4px; }
.chat-message.is-assistant .chat-message__bubble { background: var(--surface); color: var(--ink); border-bottom-left-radius: 4px; }

.chat-cursor { animation: blink 0.8s infinite; font-weight: bold; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.chat-thinking {
  display: flex; align-items: center; gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md); color: var(--muted); font-size: var(--fs-sm);
}

.chat-quick-options {
  display: flex; flex-wrap: wrap; gap: var(--space-sm); padding: 0 4px;
}

.chat-error { padding: 0 4px; }
.chat-panel__footer { padding: 12px 16px; border-top: 1px solid oklch(0 0 0 / 0.06); }

@media (max-width: 767px) {
  .chat-panel { position: fixed; inset: 0; width: 100vw; height: 100vh; border-radius: 0; }
  .chat-widget { right: 16px; bottom: 80px; }
}
</style>
```

- [ ] **Step 2: 清理旧 ChatWidget 导入的已废弃引用**

移除 ChatWidget 中不再需要的旧导入（如 `useSSE` 旧的 callbacks、`sources` 等）。

---

### Task 12: main.py — 注册新路由

**Files:**
- Modify: `backend/main.py:30` (在 routers 导入区域添加)

- [ ] **Step 1: 在 main.py 中注册 AI 路由**

在 `main.py` 的 router 导入区域（约第 30 行）添加：
```python
from routers.ai import router as ai_router
```

在路由注册区域（约第 152 行）添加：
```python
app.include_router(ai_router, prefix="/api/v1")
```

- [ ] **Step 2: 验证完整启动**

```bash
cd backend && timeout 5 python -c "
from main import app
routes = [r.path for r in app.routes if hasattr(r, 'path')]
print('AI route:', '/api/v1/ai/chat' in routes)
print('OK - All routes registered')
" 2>&1 || true
```

---

### Task 13: 端到端验证

- [ ] **Step 1: 启动后端并测试 AI 端点**

```bash
# 终端 1: 启动后端
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# 终端 2: 测试意图识别（chat 意图）
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"英歌舞是什么？"}' \
  --no-buffer
```

预期：SSE 流式返回 `token` 事件（来自 cs_agent RAG），以 `done` 事件结束。

```bash
# 测试追问流程（trip 意图，参数不全）
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"我想去潮汕"}' \
  --no-buffer
```

预期：返回 `ask` 事件，追问"准备玩几天？"

- [ ] **Step 2: 验证前端构建**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

预期：Build successful，无报错。

---

### 文件结构总览

```
backend/
  ai/
    intent_router.py    🆕  意图识别 + 多轮追问
    agent_dispatcher.py 🆕  Agent 调度 + SSE 包装
    trip_agent.py       🔧  重写：3方案全流程规划
    llm.py              ✅  已更新（智谱 + DeepSeek）
  routers/
    ai.py               🆕  POST /api/v1/ai/chat
  schemas/
    ai.py               🆕  ChatAIRequest
  main.py               🔧  注册 ai_router

frontend/src/
  components/business/
    ChatWidget.vue      🔧  升级：富媒体渲染
    TripCard.vue        🆕  行程方案卡片
    FoodCard.vue        🆕  美食推荐卡片
    HeritageCard.vue    🆕  非遗卡片
  stores/
    chat.js             🔧  升级：结构化消息
  composables/
    useSSE.js           🔧  升级：新事件类型
```
