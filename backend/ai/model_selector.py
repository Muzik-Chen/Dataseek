"""
ModelSelector — 三层降级链，为每个推理等级自动选择可用模型。

推理等级:
    high — Orchestrator + Route Agent（复杂推理）
    low  — Food Agent + Hotel Agent（简单 tool-calling）

降级逻辑:
    1. 按 MODEL_CHAIN_HIGH / MODEL_CHAIN_LOW 顺序尝试
    2. 成功创建实例 → 返回
    3. 失败 → 记录警告 → 下一个提供商
    4. 全部失败 → 抛出 RuntimeError

支持的提供商:
    zhipu    — 智谱 AI (glm-4-plus, glm-4-flash)
    deepseek — DeepSeek (deepseek-chat)
    qwen     — 阿里千问 / DashScope (qwen-max, qwen-turbo)
"""
import logging
from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# 提供商 → 创建 LLM 的工厂函数映射（延迟导入，避免循环依赖）
_PROVIDER_FACTORIES: dict[str, callable] = {}


def _ensure_factories():
    """延迟注册工厂函数（避免启动时的循环导入）。"""
    if _PROVIDER_FACTORIES:
        return

    def _make_zhipu(model_name: str, **kwargs):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            api_key=settings.ZHIPU_API_KEY,
            base_url="https://open.bigmodel.cn/api/paas/v4/",
            **kwargs,
        )

    def _make_deepseek(model_name: str, **kwargs):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1",
            **kwargs,
        )

    def _make_qwen(model_name: str, **kwargs):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            api_key=settings.QWEN_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            **kwargs,
        )

    _PROVIDER_FACTORIES["zhipu"] = _make_zhipu
    _PROVIDER_FACTORIES["deepseek"] = _make_deepseek
    _PROVIDER_FACTORIES["qwen"] = _make_qwen


def _parse_model_chain(chain_str: str) -> list[tuple[str, str]]:
    """解析模型链字符串 'zhipu:glm-4-plus,deepseek:deepseek-chat' → [(provider, model), ...]"""
    result = []
    for item in chain_str.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            provider, model = item.split(":", 1)
            result.append((provider.strip(), model.strip()))
        else:
            logger.warning(f"[ModelSelector] Invalid chain entry (missing ':'): {item}")
    return result


def get_llm(
    temperature: float = 0.7,
    streaming: bool = True,
    request_timeout: int = 30,
    max_tokens: int | None = None,
    model_kwargs: dict | None = None,
    reasoning_level: str = "high",
):
    """
    获取 LLM 实例，支持按推理等级自动选择模型 + 三层降级。

    Args:
        temperature: 生成温度（0-1）
        streaming: 是否启用流式输出
        request_timeout: HTTP 请求超时秒数
        max_tokens: 最大输出 token 数
        model_kwargs: 额外传给 ChatOpenAI 的参数
        reasoning_level: "high" 或 "low" — 决定使用哪个模型链

    Returns:
        LLM 实例（兼容 LangChain BaseChatModel 接口）

    Raises:
        RuntimeError: 模型链中所有提供商都不可用
    """
    _ensure_factories()

    chain_str = settings.MODEL_CHAIN_HIGH if reasoning_level == "high" else settings.MODEL_CHAIN_LOW
    chain = _parse_model_chain(chain_str)

    if not chain:
        raise RuntimeError(f"[ModelSelector] 模型链为空 (reasoning_level={reasoning_level})")

    kwargs = dict(
        temperature=temperature,
        streaming=streaming,
        request_timeout=request_timeout,
    )
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if model_kwargs is not None:
        kwargs["model_kwargs"] = model_kwargs

    last_error = None
    for provider, model_name in chain:
        factory = _PROVIDER_FACTORIES.get(provider)
        if factory is None:
            logger.warning(f"[ModelSelector] 未知提供商 '{provider}'，跳过")
            continue

        try:
            llm = factory(model_name, **kwargs)
            logger.info(f"[ModelSelector] ✓ 使用 {provider}:{model_name} (reasoning={reasoning_level})")
            return llm
        except Exception as e:
            last_error = e
            logger.warning(
                f"[ModelSelector] ✗ {provider}:{model_name} 不可用: {e}，尝试下一个..."
            )
            continue

    raise RuntimeError(
        f"[ModelSelector] 模型链 ({reasoning_level}) 中所有提供商均不可用。"
        f"最后错误: {last_error}"
    )
