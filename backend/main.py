"""
潮汕文化宣传平台 — FastAPI 应用入口。

启动:
    cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy import text

from config import get_settings
from database import engine

settings = get_settings()

# 国内 HuggingFace 镜像 — 必须在所有 AI 模块导入前写入 os.environ
# （routers.ai → agent_dispatcher → food_recommend 会间接导入 huggingface_hub，
#   而 huggingface_hub 在 import 时读取 HF_ENDPOINT 并缓存，之后修改无效）
if settings.HF_ENDPOINT:
    os.environ["HF_ENDPOINT"] = settings.HF_ENDPOINT

# --- Routers ---
from routers.food import router as food_router
from routers.heritage import router as heritage_router
from routers.auth import router as auth_router
from routers.user import router as user_router
from routers.chat import router as chat_router
from routers.trip import router as trip_router
from routers.community import router as community_router
from routers.message import router as message_router
from routers.dashboard import router as dashboard_router
from routers.admin import router as admin_router
from routers.festival import router as festival_router
from routers.ai import router as ai_router
from routers.hotel import router as hotel_router
<<<<<<< HEAD
from routers.upload import router as upload_router
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22


async def init_db():
    """从 SQL 文件建表 — 保留 FULLTEXT 索引、生成列等 MySQL 特性。"""
    import os
    sql_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "init_db.sql"
    )
    if not os.path.exists(sql_path):
        print(f"[DB] SQL 文件不存在: {sql_path}，回退到 ORM create_all")
        from database import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return

    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # 去掉行注释，避免拆分语句时把注释行当前导跳过
    lines = [l for l in sql.split("\n") if not l.strip().startswith("--")]
    clean_sql = "\n".join(lines)

    async with engine.begin() as conn:
        for statement in clean_sql.split(";"):
            stmt = statement.strip()
            if stmt:
                try:
                    await conn.execute(text(stmt))
                except Exception as e:
                    err_msg = str(e).lower()
                    if not any(kw in err_msg for kw in
                               ["already exists", "duplicate", "1050"]):
                        print(f"[DB] skip: {stmt[:60].split(chr(10))[0]} — {e}")


async def init_ai_modules():
    """初始化 AI 模块 — 预加载 Embedding 模型 + FAISS 索引 + RAG Chain。"""
    try:
        from ai.embeddings import get_embedding_model
        get_embedding_model()
        print("[AI] Embedding 模型加载完成")

        from ai.vector_store import load_knowledge_base
        kb = load_knowledge_base()
        if kb is not None:
            print("[AI] FAISS 知识库加载完成")
        else:
            print("[AI] FAISS 知识库不可用，将使用纯 LLM 降级模式")

        from ai.cs_agent import init_rag_chain
        await init_rag_chain()
        print("[AI] RAG Chain 初始化完成")

        from ai.trip_agent import get_trip_app
        get_trip_app()
        print("[AI] TripAgent 初始化完成")
    except Exception as e:
        print(f"[AI] 初始化部分失败（将使用降级方案）: {e}")


async def cleanup_expired_sessions():
    """清理 7 天未活动的 chat_sessions — 标记为 closed。"""
    try:
        from datetime import timedelta
        from sqlalchemy import update
        from models.session import ChatSession

        cutoff = datetime.now() - timedelta(days=7)
        async with engine.begin() as conn:
            result = await conn.execute(
                update(ChatSession)
                .where(
                    ChatSession.updated_at < cutoff,
                    ChatSession.status == 'active',
                )
                .values(status='closed')
            )
            if result.rowcount:
                print(f"[Cleanup] 已将 {result.rowcount} 个过期会话标记为 closed")
    except Exception as e:
        print(f"[Cleanup] 会话清理失败: {e}")


def setup_scheduler():
    """配置 APScheduler 定时任务。"""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from utils.weather_fetcher import register_scheduler_jobs

        scheduler = AsyncIOScheduler()
        register_scheduler_jobs(scheduler)
        scheduler.start()
        print("[Scheduler] APScheduler 已启动")
        return scheduler
    except Exception as e:
        print(f"[Scheduler] 启动失败: {e}")
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    await init_db()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    await init_ai_modules()
    await cleanup_expired_sessions()
    scheduler = setup_scheduler()
    app.state.scheduler = scheduler
    yield
    # 关闭时
    if scheduler:
        scheduler.shutdown(wait=False)
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# --- CORS ---
# 开发环境：覆盖所有本地地址变体 (localhost / 127.0.0.1 / [::1])
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
_local_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://[::1]:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://[::1]:4173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(origins + _local_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 静态文件（上传目录） ---
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# --- 注册路由 ---
app.include_router(food_router, prefix="/api/v1")
app.include_router(heritage_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(trip_router, prefix="/api/v1")
app.include_router(community_router, prefix="/api/v1")
app.include_router(message_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(festival_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(hotel_router, prefix="/api/v1")
<<<<<<< HEAD
app.include_router(upload_router, prefix="/api/v1")
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22


# --- 健康检查 ---
@app.get("/api/v1/health", tags=["系统"])
async def health():
    return {"code": 0, "message": "ok", "data": {"status": "healthy", "version": settings.APP_VERSION}}
