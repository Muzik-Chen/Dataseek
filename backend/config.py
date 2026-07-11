"""
应用配置 — 全部配置项通过环境变量注入，提供合理默认值用于开发环境。
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # --- 应用 ---
    APP_NAME: str = "潮汕文化宣传平台"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # --- 数据库 ---
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "chaoshan_platform"
    DB_POOL_SIZE: int = 10
    DB_ECHO: bool = False

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    # --- JWT ---
    # ⚠️ 生产环境务必通过环境变量 JWT_SECRET 注入强密钥，不要使用默认值
    # 生成方式: python -c "import secrets; print(secrets.token_hex(32))"
    JWT_SECRET: str = "change-me-in-production-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # --- LLM ---
    LLM_PROVIDER: str = "zhipu"          # zhipu | deepseek
    ZHIPU_MODEL: str = "glm-4-flash"
    ZHIPU_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_API_KEY: str = ""
    QWEN_API_KEY: str = ""               # Phase 6: 千问 DashScope API Key (备用)
    # 模型后备链 — 格式: "provider:model,provider:model,..."
    MODEL_CHAIN_HIGH: str = "zhipu:glm-4-plus,deepseek:deepseek-chat,qwen:qwen-max"
    MODEL_CHAIN_LOW: str = "zhipu:glm-4-flash,deepseek:deepseek-chat,qwen:qwen-turbo"

    # --- 163 SMTP 邮件 ---
    SMTP_SERVER: str = "smtp.163.com"
    SMTP_PORT: int = 465
    SMTP_USERNAME: str = ""       # 163 邮箱地址
    SMTP_PASSWORD: str = ""       # 163 SMTP 授权码（非登录密码）
    SMTP_FROM: str = ""           # 发件人（同 SMTP_USERNAME）

    # --- 天气 API ---
    WEATHER_API_KEY: str = ""

    # --- AI Feature Flags ---
    ENABLE_ROUTE_ENRICHER: bool = True   # Phase 2: 路线富化（天气/美食/非遗/酒店/人流）
    PARALLEL_PLAN_GENERATION: bool = True  # Phase 5.2: 并行生成方案
    MAX_CONCURRENT_PLANS: int = 3          # Phase 5.2: 最大并行方案数
    PLAN_MAX_RETRIES: int = 1              # Phase 5.2: 单方案失败最大重试次数

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # --- 上传 ---
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 5

    # HuggingFace 镜像
    HF_ENDPOINT: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
