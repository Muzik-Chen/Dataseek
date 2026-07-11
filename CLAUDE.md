# CLAUDE.md

## 项目概述

潮汕文化宣传平台 — 以 AI 为引擎的一站式潮汕文化服务平台。Vue 3 + FastAPI + MySQL + LangChain/LangGraph，8 个功能模块（首页/美食推荐/非遗民俗/智能客服/用户中心/行程规划/社区推荐/数据大屏）。

## Design Context

> 详细内容见 `PRODUCT.md`

- **Register**: `product` — 设计服务于功能，但功能本身可以很美
- **品牌气质**: 鲜活 / 热烈 / 有冲击力 — 灵感来自潮汕文化本身（英歌舞、工夫茶、骑楼、牛肉火锅）
- **目标用户**: 游客（快速查阅）+ 文化爱好者（深度探索），双群体同等重要
- **反参考**: 拒绝性冷淡极简 + SaaS 模板套路 + AI 默认奶油色审美 + 文艺书店风
- **五项设计原则**:
  1. **文化即组件** — UI 元素从潮汕文化中生长，Element Plus 是骨架，潮汕文化是血肉
  2. **热闹但有秩序** — 色彩可以浓烈，信息层级必须清晰
  3. **双速设计** — 同一页面支持 30 秒速览和 30 分钟沉浸两种节奏
  4. **AI 是向导不是主人** — AI 是增强层，传统浏览路径始终可用
  5. **移动端原生体验** — 游客场景以手机优先，触控友好，加载轻量
- **DESIGN.md** 尚未生成，运行 `/impeccable document` 可播种或扫描

## 技术栈实现说明

> 详细技术文档见 `技术文档/一人开发精简文档.md` 和 `技术文档/前端组件设计文档.md`

| 层级 | 文档要求 | 实际选型 | 说明 |
|------|---------|---------|------|
| LLM 服务 | Qwen3 / DeepSeek | **智谱 AI (GLM-4-Flash)** | OpenAI 兼容协议，通过 `LLM_PROVIDER` 环境变量可切换 |
| Embedding | BAAI/bge-small-zh-v1.5 | 同文档 | CPU 运行，384 维向量 |
| 向量库 | FAISS (CPU) | 同文档 | 启动时自动构建索引，持久化到 `ai/faiss_index/` |
| 知识库格式 | JSON (各 20-30 条) | **JSON + Markdown 双格式** | JSON 结构化为主要检索源 (25 条美食 + 26 条文化)，MD 为补充 |
| Service 层 | 独立 `services/` 目录 | 已建立 | 重点模块 (auth/food/trip/community) 已抽离，简单 CRUD 保留在 router |
| 前端组件 | 21 个 | 22 个 (含 TripCard) | SortDropdown/Pagination 已添加为通用组件 |
| API 端点 | 67 个 (前台 47 + 后台 20) | 已全覆盖 | 含 logout / reset-password / post-edit / comment-delete / message-read |
| 短信验证 | 阿里云 SMS | **开发阶段固定验证码 123456** | config.py 预留 SMS 配置，生产切换只需改环境变量 |

**关键目录**:
- `backend/services/` — 业务逻辑层 (auth_service / food_service / trip_service / community_service)
- `backend/ai/knowledge/` — RAG 知识库 (food_knowledge.json 25 条 + culture_knowledge.json 26 条)
- `frontend/src/components/common/` — 通用组件 (含 SortDropdown / Pagination / EmptyState / LoadingSkeleton 等)
- `data/init_db.sql` — 16 张表的完整 DDL