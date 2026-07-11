"""
意图路由器 — LLM 分析用户输入，识别意图、提取参数、判断是否需要多轮追问。

Intent 类型:
    chat     — 文化问答、闲聊 → cs_agent (RAG)
    trip     — 行程规划 → trip_agent (3方案)
    food     — 美食推荐 → food_recommend
    heritage — 非遗/民俗查询 → cs_agent (RAG)
    festival — 民俗节庆查询 → cs_agent (RAG)

多意图支持:
    LLM 返回排序后的意图列表（含置信度），primary 为最高置信度意图。
    前端最多展示 3 个按钮，对话中动态调整主次。
"""
import json
import re
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from sqlalchemy import select, update

from ai.llm import get_llm
from ai.prompts import ROUTER_PROMPT, INTENT_SCHEMA, clean_json
from database import async_session_factory
from models.chat import ChatMessage

# 多轮追问上限
MAX_TURNS = 6

# 有效意图类型
VALID_INTENTS = {"food", "heritage", "festival", "trip", "chat"}


# === DB helpers（替代原 _sessions 内存字典）===

async def _get_session_state(session_id: str) -> dict | None:
    """从 chat_sessions 表中加载会话状态。"""
    from models.session import ChatSession
    async with async_session_factory() as db:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.session_id == session_id,
                ChatSession.status == 'active',
            )
        )
        session = result.scalar()
        if session and session.intent_state:
            state = dict(session.intent_state)
            state['session_id'] = session_id
            return state
    return None


async def _save_session_state(session_id: str, state: dict, user_id: int | None = None):
    """保存或更新 chat_sessions 行。"""
    from models.session import ChatSession
    async with async_session_factory() as db:
        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        row = result.scalar()
        if row:
            row.intent_state = state
            row.updated_at = datetime.now()
        else:
            db.add(ChatSession(
                session_id=session_id,
                user_id=user_id,
                title='新对话',
                intent_state=state,
                status='active',
            ))
        await db.commit()


async def _get_chat_history(session_id: str, limit: int = 20) -> list[dict]:
    """从 chat_messages 表加载最近对话历史。"""
    async with async_session_factory() as db:
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        return [
            {"user": r.content[:200] if r.role == 'user' else '',
             "intent": '',
             "ai_summary": r.content[:150] if r.role == 'assistant' else ''}
            for r in reversed(rows)
        ]


@dataclass
class IntentResult:
    intent: str = "chat"                      # 主意图（向后兼容，= intents[0].intent）
    intents: list[dict] = field(default_factory=list)  # [{intent, confidence, primary}, ...]
    extracted_params: dict = field(default_factory=dict)
    missing_params: list[str] = field(default_factory=list)
    follow_up_question: str | None = None
    quick_options: list[str] | None = None
    interest_hints: list[str] = field(default_factory=list)  # Phase 2: 用户兴趣关键词

    def __post_init__(self):
        """确保 intent 与 intents 一致，intents 为权威来源。"""
        if self.intents:
            # 有 intents → intent 从 primary 推导
            primary = next((i for i in self.intents if i.get("primary")), None)
            self.intent = primary["intent"] if primary else self.intents[0]["intent"]
        elif self.intent:
            # 无 intents → 从 intent 构建
            self.intents = [{"intent": self.intent, "confidence": 1.0, "primary": True}]
        else:
            self.intent = "chat"
            self.intents = [{"intent": "chat", "confidence": 1.0, "primary": True}]


async def route_intent(session_id: str, user_message: str) -> IntentResult:
    """分析用户消息 → 返回 IntentResult。

    如果当前 session 存在多轮状态且参数已部分收集，
    则将新消息合并到 collected_params 中继续收集。
    同时记录对话历史用于上下文感知的意图识别。
    """
    state = await _get_session_state(session_id)

    # 如果已有活跃的多轮追问会话，优先用 LLM 提取新参数
    if state and state.get("intent") and state.get("collected_params"):
        result = await _continue_collecting(state, user_message)
        await _store_exchange(session_id, user_message, result)
        return result

    # 首次分析意图（含历史上下文）
    result = await _classify_intent(session_id, user_message)
    await _store_exchange(session_id, user_message, result)
    return result


async def _store_exchange(session_id: str, user_message: str, result: IntentResult):
    """记录一轮对话交换到 chat_sessions 状态中。"""
    state = await _get_session_state(session_id) or {}
    if "recent_exchanges" not in state:
        state["recent_exchanges"] = []
    state["recent_exchanges"].append({
        "user": user_message[:500],
        "intent": result.intent,
        "intents": result.intents,
    })
    if len(state["recent_exchanges"]) > 20:
        state["recent_exchanges"] = state["recent_exchanges"][-20:]
    await _save_session_state(session_id, state)


def _simple_extract(missing: list[str], user_message: str) -> dict:
    """本地模式匹配提取参数 — 快速、可靠、零 API 调用。

    处理绝大多数常见回答（"3天""家人""美食文化"…），
    仅匹配失败时才回退到 LLM 提取。
    """
    if not missing:
        return {}
    result = {}
    msg = user_message.strip()

    for param in missing:
        if param == "days":
            m = re.search(r"(\d+)\s*天", msg)
            if m:
                result["days"] = int(m.group(1))

        elif param == "crowd_type":
            family_words = ["家人", "家庭", "爸妈", "父母", "孩子", "小孩", "一家", "亲子",
                            "爸爸", "妈妈", "亲戚", "长辈", "和家", "全家"]
            couple_words = ["情侣", "对象", "女朋友", "男朋友", "老公", "老婆", "恋人", "二人世界"]
            friends_words = ["朋友", "同学", "同事", "闺蜜", "兄弟", "哥们", "好友", "伙伴"]
            single_words = ["自己", "一个人", "独自", "单人", "独行", "solo"]

            if any(w in msg for w in family_words):
                result["crowd_type"] = "family"
            elif any(w in msg for w in couple_words):
                result["crowd_type"] = "couple"
            elif any(w in msg for w in friends_words):
                result["crowd_type"] = "friends"
            elif any(w in msg for w in single_words):
                result["crowd_type"] = "single"

        elif param == "interests":
            interests = []
            food_kw = ["美食", "吃", "小吃", "牛肉", "火锅", "肠粉", "粿", "蚝烙", "卤鹅", "好食"]
            culture_kw = ["文化", "历史", "古迹", "非遗", "民俗", "传统", "古城", "牌坊", "英歌",
                          "工夫茶", "潮剧", "祠堂", "寺庙", "骑楼", "老建筑"]
            nature_kw = ["自然", "风景", "山水", "海", "山", "公园", "海滩", "南澳", "生态", "徒步"]

            if any(w in msg for w in food_kw):
                interests.append("food")
            if any(w in msg for w in culture_kw):
                interests.append("culture")
            if any(w in msg for w in nature_kw):
                interests.append("nature")
            if any(w in msg for w in ["都要", "都行", "随便", "全都要", "都感兴趣", "都看看", "综合"]):
                interests = ["food", "culture", "nature"]
            if interests:
                result["interests"] = interests

        elif param == "origin":
            cities = [
                "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京",
                "厦门", "重庆", "长沙", "西安", "天津", "苏州", "郑州", "东莞",
                "佛山", "珠海", "惠州", "中山", "福州", "泉州", "漳州", "南昌",
            ]
            for city in cities:
                if city in msg:
                    result["origin"] = city
                    break
            # 也匹配 "从XX来" 模式
            m = re.search(r"从(.{2,4})(?:来|出发|过来)", msg)
            if m and "origin" not in result:
                result["origin"] = m.group(1)

    return result


async def _llm_extract(missing: list[str], collected: dict, user_message: str) -> dict:
    """LLM 兜底提取 — 仅当本地模式匹配失败时调用。"""
    llm = get_llm(temperature=0.1, streaming=False)
    prompt = f"""从用户消息中提取以下参数的值。只提取当前消息中明确提到的参数。

缺失参数：{json.dumps(missing, ensure_ascii=False)}
当前已收集：{json.dumps(collected, ensure_ascii=False)}
用户消息：{user_message}

严格输出 JSON（不要 markdown 代码块，不要注释）：
{{"参数名": "值"}}

规则：
- days 必须是整数
- crowd_type 只能是 single/couple/family/friends 之一
- interests 是字符串数组，如 ["food","culture"]
- 如果消息中未提到某个参数，不要输出它"""

    try:
        response = await asyncio.wait_for(llm.ainvoke(prompt), timeout=25)
        content = response.content if hasattr(response, "content") else str(response)
        content = clean_json(content)
        return json.loads(content)
    except (asyncio.TimeoutError, Exception):
        return {}


async def _format_history(session_id: str) -> str:
    """从 chat_messages 表加载最近对话历史，格式化为 prompt 片段。"""
    msgs = await _get_chat_history(session_id, 12)  # 最近 12 条消息（6 轮）
    if not msgs:
        return ""

    lines = ["## 对话历史（最近几轮）"]
    for i, m in enumerate(msgs, 1):
        if m['user']:
            lines.append(f"{i}. 用户：{m['user'][:200]}")
        if m.get('ai_summary'):
            lines.append(f"   AI：{m['ai_summary'][:150]}")
    return "\n".join(lines) + "\n"


async def _classify_intent(session_id: str, user_message: str) -> IntentResult:
    """意图分类 + 参数提取（结合对话历史上下文，返回多意图列表）。"""
    llm = get_llm(temperature=0.1, streaming=False)
    # 对用户输入做基本净化，防止 prompt 注入
    sanitized_message = user_message.replace("{", "&#123;").replace("}", "&#125;")[:2000]

    history_text = await _format_history(session_id)
    history_section = history_text if history_text else "（无历史对话，仅根据当前消息判断）"

    prompt = ROUTER_PROMPT.format(
        history_section=history_section,
        message=sanitized_message,
    )

    try:
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        content = clean_json(content)
        data = json.loads(content)
    except Exception:
        # LLM 失败时退化为 chat
        return IntentResult(intent="chat", intents=[{"intent": "chat", "confidence": 1.0, "primary": True}])

    # 解析 intents 数组
    intents = data.get("intents", [])
    if not intents:
        # 兼容旧的单个 intent 格式
        single_intent = data.get("intent", "chat")
        if single_intent not in VALID_INTENTS:
            single_intent = "chat"
        intents = [{"intent": single_intent, "confidence": 1.0, "primary": True}]
    else:
        # 过滤无效意图和低置信度
        intents = [
            i for i in intents
            if i.get("intent") in VALID_INTENTS and i.get("confidence", 0) > 0.35
        ]
        if not intents:
            intents = [{"intent": "chat", "confidence": 1.0, "primary": True}]
        # 确保第一个为 primary
        if not any(i.get("primary") for i in intents):
            intents[0]["primary"] = True
        # 最多保留 3 个
        intents = intents[:3]

    # primary 意图
    primary = next((i for i in intents if i.get("primary")), intents[0])
    primary_intent = primary["intent"]

    extracted = data.get("extracted_params", {})
    interest_hints = data.get("interest_hints", [])
    if not isinstance(interest_hints, list):
        interest_hints = []

    # 检查缺失参数（仅对 primary 意图）
    schema = INTENT_SCHEMA.get(primary_intent, {})
    missing = [p for p in schema.get("required", []) if p not in extracted or not extracted[p]]

    if missing:
        # 保存多轮状态到 DB（含 interest_hints 以便后续轮次使用）
        state = {
            "session_id": session_id,
            "intent": primary_intent,
            "intents": intents,
            "collected_params": extracted,
            "interest_hints": interest_hints,
            "turn": 1,
        }
        await _save_session_state(session_id, state)
        return _build_ask_result(primary_intent, intents, missing)

    # 提取兴趣关键词（Phase 2）
    interest_hints = data.get("interest_hints", [])
    if not isinstance(interest_hints, list):
        interest_hints = []

    # 参数齐全，直接执行
    return IntentResult(
        intent=primary_intent,
        intents=intents,
        extracted_params=extracted,
        missing_params=[],
        interest_hints=interest_hints,
    )


async def _continue_collecting(state: dict, user_message: str) -> IntentResult:
    """多轮对话中收集缺失参数。

    策略：本地模式匹配优先（快 + 可靠）→ LLM 兜底（仅当匹配失败时调用）。
    """
    intent = state["intent"]
    intents = state.get("intents", [{"intent": intent, "confidence": 1.0, "primary": True}])
    collected = state["collected_params"]
    schema = INTENT_SCHEMA[intent]
    state["turn"] += 1

    # 超过轮次上限 → 强制结束，用现有参数继续
    if state["turn"] > MAX_TURNS:
        await _close_session(state.get("session_id", ""))
        return IntentResult(intent=intent, intents=intents, extracted_params=collected,
                           interest_hints=state.get("interest_hints", []))

    missing = [p for p in schema["required"] if p not in collected or not collected[p]]

    # Step 1: 本地模式匹配（覆盖 90%+ 常见回答）
    new_params = _simple_extract(missing, user_message)

    # Step 2: 本地匹配未命中第一个缺失参数 → LLM 兜底
    first_missing = missing[0]
    if first_missing not in new_params:
        llm_result = await _llm_extract(missing, collected, user_message)
        new_params.update(llm_result)

    # 合并参数
    collected.update(new_params)

    # 重新计算缺失
    missing = [p for p in schema["required"] if p not in collected or not collected[p]]

    if missing:
        return _build_ask_result(intent, intents, missing)

    # 参数收集完毕 → 清理状态
    await _close_session(state.get("session_id", ""))
    return IntentResult(
        intent=intent,
        intents=intents,
        extracted_params=collected,
        missing_params=[],
        interest_hints=state.get("interest_hints", []),
    )


def _build_ask_result(intent: str, intents: list[dict] | None = None, missing: list[str] | None = None) -> IntentResult:
    """构建追问结果。"""
    if missing is None:
        missing = []
    if intents is None:
        intents = [{"intent": intent, "confidence": 1.0, "primary": True}]
    schema = INTENT_SCHEMA.get(intent, {})
    first_missing = missing[0] if missing else ""
    q = schema.get("questions", {}).get(first_missing, {})
    return IntentResult(
        intent=intent,
        intents=intents,
        missing_params=missing,
        follow_up_question=q.get("text", f"请提供{first_missing}" if first_missing else None),
        quick_options=q.get("options"),
    )


async def enrich_last_exchange(session_id: str, ai_summary: str):
    """用 AI 回答的摘要补充最近一轮对话记录（在流式响应完成后调用）。"""
    state = await _get_session_state(session_id) or {}
    exchanges = state.get("recent_exchanges", [])
    if exchanges:
        exchanges[-1]["ai_summary"] = ai_summary[:300]
        await _save_session_state(session_id, state)


async def _close_session(session_id: str):
    """标记 session 为已关闭。"""
    if not session_id:
        return
    from models.session import ChatSession
    async with async_session_factory() as db:
        await db.execute(
            update(ChatSession)
            .where(ChatSession.session_id == session_id)
            .values(status='closed', updated_at=datetime.now())
        )
        await db.commit()


async def clear_session(session_id: str):
    """清除多轮对话状态。"""
    await _close_session(session_id)
