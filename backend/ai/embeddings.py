"""
Embedding 模型加载 — BGE 中文小模型，本地 CPU 运行。
首次下载约 400MB，后续启动直接加载本地缓存。

国内网络环境：如果 HuggingFace Hub 直连失败，设置环境变量:
    HF_ENDPOINT=https://hf-mirror.com
"""
import os

# 国内 HuggingFace 镜像 — 必须在 import HuggingFaceEmbeddings 前设置
# pydantic-settings 加载 .env 时可能不会自动注入 os.environ
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from langchain_community.embeddings import HuggingFaceEmbeddings

# 全局单例
_embedding_model: HuggingFaceEmbeddings | None = None
_embedding_failed: bool = False


def get_embedding_model() -> HuggingFaceEmbeddings | None:
    """获取 BGE 中文 Embedding 模型（单例）。

    bge-small-zh-v1.5：384 维向量，CPU 单条编码 < 50ms。
    首次调用时自动下载到本地缓存（~400MB），后续启动直接加载。
    下载失败时返回 None — 上层调用方（RAG）会降级为纯 LLM 模式。
    """
    global _embedding_model, _embedding_failed

    if _embedding_model is not None:
        return _embedding_model

    if _embedding_failed:
        return None

    try:
        # local_files_only=True: 禁止在线检查模型更新，避免网络不稳定时
        # SentenceTransformer.__init__ 阻塞数分钟导致整个后端无法启动。
        # 首次运行模型未缓存时，该参数会导致异常 → 外层 catch 降级为 None。
        _embedding_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-zh-v1.5",
            model_kwargs={"device": "cpu", "local_files_only": True},
            encode_kwargs={"normalize_embeddings": True},
        )
        return _embedding_model
    except Exception as e:
        _embedding_failed = True
        err_msg = str(e).lower()
        hint = ""
        if "local_files_only" in err_msg or "can't load" in err_msg or "not found" in err_msg:
            hint = (
                "\n   💡 首次运行需要先下载 Embedding 模型（~400MB）："
                "\n      1. python -c \"from sentence_transformers import SentenceTransformer;"
                "\n         SentenceTransformer('BAAI/bge-small-zh-v1.5')\""
                "\n      2. 或设置环境变量 HF_ENDPOINT=https://hf-mirror.com 加速下载"
                "\n      3. 下载完成后重启后端，将自动加载本地缓存"
            )
        elif "connection" in err_msg or "timeout" in err_msg:
            hint = (
                "\n   💡 网络连接失败，可尝试："
                "\n      1. 检查 HF_ENDPOINT 环境变量是否可访问"
                "\n      2. 当前镜像: https://hf-mirror.com"
            )
        print(f"[AI] Embedding 模型加载失败（RAG 将降级为纯 LLM 模式）: {e}{hint}")
        return None
