# AI 全局智能聊天浮窗 · 设计文档

**日期**: 2026-07-06  
**状态**: 待审核  
**关联**: 潮汕文化宣传平台 · Vue 3 + FastAPI + LangChain/LangGraph

---

## 1. 概述

### 1.1 目标

将现有的 `ChatWidget.vue`（仅对接通用客服 RAG）升级为**全站 AI 统一入口**：
- 用户在浮窗内自由输入，后端 LLM 自动识别意图 → 路由到对应 AI Agent
- 支持文化问答、美食推荐、非遗查询、**全流程旅行规划**（出发地→交通→酒店→每日行程，3 套方案对比）
- 回复不仅是文字，包含可交互的富媒体卡片（行程卡、美食卡、非遗卡）
- 信息不全时主动多轮追问，信息齐备时直接执行

### 1.2 设计原则

- **智能路由** — 一个端点、一个浮窗、一切都是对话
- **混合模式对话** — 一句话能说清就直接出结果，说不清就多轮引导
- **富媒体但不臃肿** — 卡片可交互但不替代完整页面，点击可跳转详情
- **复用现有 AI 模块** — `cs_agent.py`、`trip_agent.py`、`food_recommend.py` 保留，上层加调度

---

## 2. 总体架构

```
┌──────────────────────────────────────────────────────┐
│                    Frontend                          │
│  ChatWidget.vue ──▶ chatStore ──▶ useSSE ──▶ fetch  │
│       │                                             │
│       ├── TripCard.vue    (行程卡片)                  │
│       ├── FoodCard.vue    (美食推荐卡片)              │
│       └── HeritageCard.vue (非遗卡片)                 │
└──────────────────────┼──────────────────────────────┘
                       │ SSE stream
┌──────────────────────┼──────────────────────────────┐
│                      ▼         Backend              │
│  POST /api/v1/ai/chat  (统一 AI 入口 · SSE 流式)      │
│       │                                             │
│       ▼                                             │
│  IntentRouter (LLM 意图识别 + 参数提取 + 追问判断)     │
│       │                                             │
│       ▼                                             │
│  AgentDispatcher (根据 intent 分发)                   │
│       │                                             │
│       ├── intent=chat     → cs_agent.py (RAG + LLM) │
│       ├── intent=trip     → trip_agent.py (3方案)    │
│       ├── intent=food     → food_recommend.py        │
│       └── intent=heritage → cs_agent.py (RAG + LLM) │
└──────────────────────────────────────────────────────┘
```

---

## 3. 后端设计

### 3.1 新增模块

#### 3.1.1 `ai/intent_router.py` — 意图路由器

**职责**: 分析用户输入 → 输出 intent + 参数 + 是否需追问

**输入**: `session_id` + `user_message` + 会话上下文（多轮状态）

**输出**:
```python
class IntentResult:
    intent: str          # "chat" | "trip" | "food" | "heritage"
    extracted_params: dict  # 已提取的参数
    missing_params: list    # 缺失的必要参数
    follow_up_question: str | None  # 追问文本
    quick_options: list | None      # 快捷选项
```

**意图判断逻辑**（用轻量 LLM 调用实现）:

| Intent | 触发条件 | 必要参数 | 追问策略 |
|--------|---------|---------|---------|
| `trip` | 行程/旅游/出行/玩几天 | origin, days, crowd_type, interests | 逐一追问缺失项，提供快捷选项 |
| `food` | 推荐/吃什么/哪里好吃 | preference(可选) | 偏好不明确时追问口味/预算 |
| `heritage` | 非遗/民俗/传统/文化 | keyword | 直接检索，通常不追问 |
| `chat` | 其他问答/闲聊 | 无 | 直接 RAG |

**多轮状态存储**（内存 dict，key=session_id）:
```python
{
    "session_id": "abc123",
    "intent": "trip",
    "collected_params": {"days": 3, "crowd_type": "family"},
    "missing_params": ["origin", "interests"],
    "turn": 3
}
```

#### 3.1.2 `ai/agent_dispatcher.py` — Agent 调度器

**职责**: 接收 IntentRouter 结果 → 调用对应 Agent → 统一包装为 SSE 事件流

```python
async def dispatch(session_id: str, intent: str, params: dict) -> AsyncGenerator[str, None]:
    yield sse_event("thinking", label="正在为您准备...")
    
    if intent == "trip":
        async for event in run_trip_agent(params):
            yield event
    elif intent == "food":
        async for event in run_food_agent(params):
            yield event
    elif intent in ("chat", "heritage"):
        async for event in run_cs_agent(session_id, params):
            yield event
    
    yield sse_event("done", session_id=session_id, intent=intent)
```

#### 3.1.3 `ai/trip_agent.py` — 行程规划重写

**从**: 单方案生成（填参数 → 一个 JSON）
**升级为**: 多方案全流程规划

**新增输入参数**:
- `origin: str` — 出发城市
- `budget: str` — 预算档位 (budget/mid/luxury)
- `interests: list[str]` — 兴趣偏好

**三套方案命名规则**:
| 方案 | 主题 | 侧重区域 |
|------|------|---------|
| 方案A | 深度美食 | 汕头市区 + 南澳 |
| 方案B | 文化寻根 | 潮州古城 + 龙湖 |
| 方案C | 全景环游 | 汕潮揭三市精华 |

**每套方案 JSON 结构**:
```json
{
  "plan_id": "A",
  "title": "汕头深度美食之旅",
  "theme": "美食+市井",
  "summary": "4天3晚，沉浸式体验潮汕美食之都...",
  "transport": {
    "to": {"mode": "高铁", "route": "深圳北→潮汕站", "duration": "2h", "cost": 150},
    "return": {"mode": "高铁", "route": "汕头站→深圳北", "duration": "2h", "cost": 150}
  },
  "hotels": [
    {"name": "汕头君华酒店", "stars": 4, "price": 350, "level": "comfort", "reason": "位于市中心，步行可达小公园"},
    {"name": "汕头如家精选", "stars": 3, "price": 180, "level": "budget", "reason": "性价比高，近公交枢纽"},
    {"name": "汕头国际大酒店", "stars": 5, "price": 600, "level": "luxury", "reason": "海景房，顶级设施"}
  ],
  "days": [
    {
      "day": 1,
      "title": "初识汕头·老城烟火",
      "activities": [
        {"time": "09:00", "name": "抵达+入住", "type": "transport", "description": "高铁抵达潮汕站，打车30分钟前往酒店"},
        {"time": "11:00", "name": "小公园骑楼群", "type": "scenery", "description": "...", "reason": "..."},
        {"time": "12:30", "name": "八合里牛肉火锅(总店)", "type": "food", "description": "...", "cost": "¥80/人"}
      ]
    }
  ],
  "estimated_cost": {"transport": 300, "hotel": 1400, "food": 800, "tickets": 200, "total": 2700},
  "tips": ["12月汕头气温15-22°C，建议带薄外套", "热门火锅店需排队，建议错峰前往"]
}
```

#### 3.1.4 `routers/ai.py` — 统一 AI 路由端点

```python
@router.post("/ai/chat")
async def ai_chat(req: ChatAIRequest):
    """统一 AI 聊天入口 — SSE 流式返回。"""
    return StreamingResponse(
        chat_pipeline(req.session_id, req.message),
        media_type="text/event-stream",
        ...
    )
```

**请求体**: `{ "message": str, "session_id": str | None }`

### 3.2 SSE 事件协议

| 事件类型 | 方向 | 说明 | 数据字段 |
|---------|------|------|---------|
| `thinking` | 后端→前端 | AI 正在思考 | `label: str` |
| `ask` | 后端→前端 | 多轮追问 | `question: str`, `options: list[str]?` |
| `token` | 后端→前端 | 流式文字 | `content: str` |
| `trip_card` | 后端→前端 | 行程方案卡片 | `plans: list[dict]` (3套方案) |
| `food_card` | 后端→前端 | 美食推荐卡片 | `items: list[dict]` |
| `heritage_card` | 后端→前端 | 非遗介绍卡片 | `item: dict` |
| `done` | 后端→前端 | 本轮完成 | `session_id: str`, `intent: str` |
| `error` | 后端→前端 | 错误 | `message: str` |

### 3.3 LLM 配置需求

| 配置项 | 用途 | 需要用户提供 |
|--------|------|-------------|
| `DASHSCOPE_API_KEY` | Qwen 通义千问 API Key | **需要** |
| `DEEPSEEK_API_KEY` | DeepSeek API Key（备选） | 可选 |
| `LLM_PROVIDER` | 选择 LLM 服务商 (qwen/deepseek) | qwen 即可 |

> 目前 `.env` 中 `DASHSCOPE_API_KEY=` 为空，需要填入有效 API Key。推荐使用阿里云百炼平台（DashScope）的 `qwen-turbo` 或 `qwen-plus`，成本低、中文效果好。

---

## 4. 前端设计

### 4.1 ChatWidget.vue — 升级改造

**保留**:
- 固定定位 FAB 按钮 + 弹窗面板结构
- SSE 流式接收 (`useSSE.js`)
- 欢迎语 + 建议问题
- 新对话 / 关闭按钮

**新增/改造**:

| 功能 | 描述 |
|------|------|
| 消息类型支持 | 消息不再只是纯文本，支持 `text` / `trip_card` / `food_card` / `heritage_card` |
| 卡片渲染区 | body 内按消息类型动态渲染对应子组件 |
| thinking 状态 | 显示"正在分析需求...""正在生成行程..."等动态状态 |
| 快捷选项 | `ask` 事件带 `options` 时，渲染为可点击按钮（如"2天""3天""4天"） |
| 底部工具栏 | 新增语音输入按钮（预留）、图片上传按钮（预留） |

### 4.2 TripCard.vue — 行程方案卡片（新增）

**Props**: `plans: TripPlan[]`

**UI 结构**:
```
┌──────────────────────────────────┐
│ 🗺️ 潮汕4日家庭旅行               │
│ 从深圳出发 · 4天 · 家庭 · 3套方案  │
├──────────────────────────────────┤
│ [方案A: 汕头深度] [方案B: 文化寻根] [方案C: 全景环游] │  ← el-tabs
├──────────────────────────────────┤
│ 🚗 交通: 深圳北→潮汕站 高铁2h ¥150 │
│ 🏨 推荐酒店(3档):                  │
│   · 君华酒店 ⭐4.5 ¥350/晚         │
│   · 如家精选 ⭐4.0 ¥180/晚         │
│   · 国际大酒店 ⭐4.8 ¥600/晚       │
├──────────────────────────────────┤
│ ▼ Day 1 · 初识汕头·老城烟火        │  ← 折叠面板，默认展开 Day1
│   09:00 抵达+入住                 │
│   11:00 小公园骑楼群 📸           │
│   12:30 八合里牛肉火锅 🍲 ¥80     │
│   ...                            │
│ ▶ Day 2 · ...                    │  ← 折叠
│ ▶ Day 3 · ...                    │
│ ▶ Day 4 · ...                    │
├──────────────────────────────────┤
│ 💰 预估: ¥2,700/人               │
│ [💾 保存到我的行程] [📋 复制] [🔄 换一换] │
└──────────────────────────────────┘
```

**交互**:
- Tab 切换方案（方案A/B/C）
- 每日行程折叠/展开
- "保存到我的行程" → 调用 `POST /api/v1/trip/plan` 存入数据库
- "复制链接" → 复制分享链接到剪贴板
- "换一换" → 用相同参数重新请求 AI（temperature 会增加随机性）
- 点击酒店/景点名称 → 如有详情页则跳转

### 4.3 FoodCard.vue — 美食推荐卡片（新增）

**Props**: `items: FoodItem[]`

**UI**: 横向滚动卡片列表，每张卡片包含图片、名称、评分、人均价格、推荐理由。"❤️收藏"按钮调用 `POST /api/v1/user/favorites`。

### 4.4 HeritageCard.vue — 非遗卡片（新增）

**Props**: `item: HeritageItem`

**UI**: 单张图文卡片，包含非遗名称、类别标签、简介、传承人、所属地区。"❤️收藏"按钮。

### 4.5 chatStore 升级

```js
// 新增状态
const currentIntent = ref(null)         // 当前对话意图
const messages = ref([])                 // 消息支持多种 type

// 消息结构
{
  id: str,
  role: 'user' | 'assistant',
  type: 'text' | 'trip_card' | 'food_card' | 'heritage_card',
  content: str | null,                  // text 类型时使用
  cardData: object | null,              // 卡片类型时使用
  time: str,
}

// 新增 actions
function saveTripPlan(planData)  // 调 POST /trip/plan
function toggleFavorite(itemType, itemId)  // 调 POST/DELETE /user/favorites
```

### 4.6 useSSE 升级

新增事件类型解析:
- `thinking` → 设置 chatStore 中 thinking 状态文本
- `ask` → 渲染快捷选项按钮
- `trip_card` → 追加 type=trip_card 消息
- `food_card` → 追加 type=food_card 消息
- `heritage_card` → 追加 type=heritage_card 消息

---

## 5. 数据流示例

### 5.1 全流程旅行规划

```
用户输入: "和家人从深圳去潮汕玩4天"
    ↓ POST /api/v1/ai/chat
IntentRouter:
    intent: "trip"
    extracted: { origin: "深圳", days: 4, crowd_type: "family" }
    missing: ["interests", "budget"]
    → SSE: {"type": "ask", "question": "主要对哪些方面感兴趣呢？", "options": ["美食🍲", "文化🏛️", "自然🌿", "都要"]}

用户点击: "美食🍲"
    ↓ POST /api/v1/ai/chat
IntentRouter:
    missing: ["budget"]
    → SSE: {"type": "ask", "question": "预算大概什么档位？", "options": ["经济实惠", "舒适为主", "高端享受"]}

用户点击: "舒适为主"
    ↓ POST /api/v1/ai/chat
IntentRouter:
    all_params_collected: { origin, days:4, crowd_type:"family", interests:["food"], budget:"mid" }
    → AgentDispatcher → trip_agent

TripAgent 生成 3 套方案:
    → SSE: {"type": "thinking", "label": "正在为您规划3套旅行方案..."}
    → SSE: {"type": "trip_card", "plans": [方案A, 方案B, 方案C]}
    → SSE: {"type": "done", "session_id": "xxx", "intent": "trip"}

用户点击: "💾 保存到我的行程" (方案A)
    → POST /api/v1/trip/plan  存入数据库
    → 成功提示
```

---

## 6. 实现范围

### 6.1 后端 — 新增/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `ai/intent_router.py` | 🆕 | LLM 意图识别 + 参数提取 + 追问逻辑 |
| `ai/agent_dispatcher.py` | 🆕 | 统一调度 + SSE 事件包装 |
| `ai/trip_agent.py` | 🔧 重写 | 单方案→3方案，加交通/酒店/费用 |
| `routers/ai.py` | 🆕 | `POST /api/v1/ai/chat` SSE 端点 |
| `schemas/ai.py` | 🆕 | ChatAIRequest schema |

### 6.2 前端 — 新增/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `components/business/ChatWidget.vue` | 🔧 升级 | 富媒体渲染 + thinking状态 + 快捷选项 |
| `components/business/TripCard.vue` | 🆕 | 多方案 Tab + 折叠/展开 + 保存 |
| `components/business/FoodCard.vue` | 🆕 | 横向滑动推荐卡片 + 收藏 |
| `components/business/HeritageCard.vue` | 🆕 | 非遗图文卡片 + 收藏 |
| `stores/chat.js` | 🔧 升级 | 结构化消息类型 + 保存/收藏 action |
| `composables/useSSE.js` | 🔧 升级 | 新增事件类型解析 |

### 6.3 不在此次范围

- 语音输入（前端按钮预留，后端 STT 后续再加）
- 图片上传识别（预留按钮）
- 酒店/交通 API 真实对接（目前 LLM 基于知识生成，后续可接入携程/12306 API）
- Admin 管理后台 AI 对话（ChatWidget 在 admin 路由不可见）

---

## 7. LLM 配置需求

需要用户提供以下信息才能运行 AI 功能：

| 配置项 | 说明 | 获取方式 |
|--------|------|---------|
| **ZHIPU_API_KEY** | 智谱 AI API Key（推荐） | 前往 [open.bigmodel.cn](https://open.bigmodel.cn) 注册 → 获取 API Key → 填入 `.env` |
| ZHIPU_MODEL | 模型型号，默认 `glm-4-flash` | 免费轻量模型，复杂任务可换 `glm-4-plus` |
| **DEEPSEEK_API_KEY** | DeepSeek API Key（备选） | 前往 [platform.deepseek.com](https://platform.deepseek.com) 注册 → 获取 API Key |
| DEEPSEEK_MODEL | 模型型号，默认 `deepseek-chat` | 无需改动 |
| LLM_PROVIDER | 设为 `zhipu` 或 `deepseek` | 默认 `zhipu` |

### 推荐配置

- **日常使用**: `LLM_PROVIDER=zhipu` + `ZHIPU_MODEL=glm-4-flash`（免费额度，适合意图路由和简单问答）
- **行程规划**: 可在 `trip_agent.py` 中单独指定使用 `glm-4-plus` 或 `deepseek-chat`（推理能力更强）
- **双模型分工**: IntentRouter 用 `glm-4-flash`（快+便宜），TripAgent 用 `deepseek-chat`（推理强）

---

## 8. 设计决策记录

| 决策 | 选项 | 选择 | 原因 |
|------|------|------|------|
| 交互方式 | A.智能路由 / B.功能菜单 / C.富媒体 | **A + C 混合** | 用户选择：智能路由，但输出带富媒体卡片 |
| 行程规划深度 | A.一问一答 / B.多轮对话 / C.混合 | **C.混合模式** | 信息全直接生成，不全则追问 |
| 前端富媒体程度 | A.纯文本 / B.功能卡片 / C.全功能 | **C.全功能嵌入式** | 卡片内可收藏、保存行程、跳转详情 |
| 后端端点 | 统一 vs 多端点 | **统一 `/api/v1/ai/chat`** | 简化前端调用，后端负责路由 |
| 行程方案数量 | 单方案 vs 多方案 | **至少3套** | 用户明确要求 |
| LLM 提供商 | Qwen vs DeepSeek | **Qwen (通义千问)** | 中文效果好、成本低、易获取 |
