"""
LLM 提供商适配层 — 统一接口，支持智谱 (ChatGLM)、DeepSeek 和千问 (DashScope)。
Phase 6: 新增 ModelSelector 三层降级链 + reasoning_level 参数。

使用方式:
    from ai.llm import get_llm
    llm = get_llm()                        # 旧接口，按 LLM_PROVIDER 配置
    llm = get_llm(reasoning_level="high")  # 新接口，按推理等级自动选模型+降级
    response = await llm.ainvoke("你好")
"""
from config import get_settings

settings = get_settings()


def get_llm(temperature: float = 0.7, streaming: bool = True, request_timeout: int = 30,
            max_tokens: int | None = None, model_kwargs: dict | None = None,
            reasoning_level: str | None = None):
    """获取 LLM 实例。

    两种模式：
    1. reasoning_level=None（默认/兼容模式）：按 LLM_PROVIDER 配置选模型
    2. reasoning_level="high"|"low"（Phase 6）：按推理等级自动选模型 + 三层降级链

    Args:
        temperature: 生成温度（0-1），越低越确定
        streaming: 是否启用流式输出
        request_timeout: HTTP 请求超时秒数（默认 30s；长文本生成建议 120s）
        max_tokens: 最大输出 token 数（None = API 默认值；长 JSON 建议 4096）
        model_kwargs: 额外传给 ChatOpenAI 的参数（如 response_format）
        reasoning_level: "high" | "low" | None — 推理等级，None 使用原有 provider 逻辑

    Returns:
        LLM 实例（兼容 LangChain BaseChatModel 接口）
    """
    # Phase 6: 使用 ModelSelector 三层降级链
    if reasoning_level is not None:
        from ai.model_selector import get_llm as _selector_get_llm
        return _selector_get_llm(
            temperature=temperature,
            streaming=streaming,
            request_timeout=request_timeout,
            max_tokens=max_tokens,
            model_kwargs=model_kwargs,
            reasoning_level=reasoning_level,
        )

    # 兼容模式：原有 provider 逻辑
    provider = settings.LLM_PROVIDER

    if provider == "zhipu":
        return _get_zhipu_llm(temperature, streaming, request_timeout, max_tokens, model_kwargs)
    elif provider == "deepseek":
        return _get_deepseek_llm(temperature, streaming, request_timeout, max_tokens, model_kwargs)
    elif provider == "qwen":
        return _get_qwen_llm(temperature, streaming, request_timeout, max_tokens, model_kwargs)
    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")


def _get_zhipu_llm(temperature: float, streaming: bool = True, request_timeout: int = 30,
                   max_tokens: int | None = None, model_kwargs: dict | None = None):
    """获取智谱 GLM LLM（兼容 OpenAI API）。

    安装依赖: pip install langchain-openai
    API 文档: https://open.bigmodel.cn/dev/api

    推荐模型:
        - glm-4-flash: 免费/低成本，适合意图路由 + 简单问答
        - glm-4-plus:  高性能，适合复杂行程规划
    """
    try:
        from langchain_openai import ChatOpenAI
        kwargs = dict(
            model=settings.ZHIPU_MODEL,
            api_key=settings.ZHIPU_API_KEY,
            base_url="https://open.bigmodel.cn/api/paas/v4/",
            temperature=temperature,
            streaming=streaming,
            request_timeout=request_timeout,
        )
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if model_kwargs is not None:
            kwargs["model_kwargs"] = model_kwargs
        return ChatOpenAI(**kwargs)
    except ImportError:
        return _PlaceholderLLM("智谱", settings.ZHIPU_MODEL)


def _get_deepseek_llm(temperature: float, streaming: bool = True, request_timeout: int = 30,
                      max_tokens: int | None = None, model_kwargs: dict | None = None):
    """获取 DeepSeek LLM（兼容 OpenAI API）。

    安装依赖: pip install langchain-openai
    """
    try:
        from langchain_openai import ChatOpenAI
        kwargs = dict(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1",
            temperature=temperature,
            streaming=streaming,
            request_timeout=request_timeout,
        )
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if model_kwargs is not None:
            kwargs["model_kwargs"] = model_kwargs
        return ChatOpenAI(**kwargs)
    except ImportError:
        return _PlaceholderLLM("DeepSeek", settings.DEEPSEEK_MODEL)


def _get_qwen_llm(temperature: float, streaming: bool = True, request_timeout: int = 30,
                  max_tokens: int | None = None, model_kwargs: dict | None = None):
    """获取千问 LLM（DashScope 兼容 OpenAI API）。

    API 文档: https://help.aliyun.com/zh/model-studio
    """
    try:
        from langchain_openai import ChatOpenAI
        kwargs = dict(
            model="qwen-turbo",  # 默认，可通过环境变量覆盖
            api_key=settings.QWEN_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            temperature=temperature,
            streaming=streaming,
            request_timeout=request_timeout,
        )
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if model_kwargs is not None:
            kwargs["model_kwargs"] = model_kwargs
        return ChatOpenAI(**kwargs)
    except ImportError:
        return _PlaceholderLLM("千问", "qwen-turbo")


class _PlaceholderLLM:
    """占位 LLM — 在 langchain 未安装时提供基本模拟，不阻塞开发。"""

    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model

    async def ainvoke(self, prompt: str) -> str:
        return f"[{self.provider}:{self.model}] 占位回复:\n{prompt[:200]}..."

    def invoke(self, prompt: str) -> str:
        return f"[{self.provider}:{self.model}] 占位回复:\n{prompt[:200]}..."
