"""
FAISS 向量库构建与加载。
FastAPI 启动时加载到内存作为全局单例。
支持 Markdown 和 JSON 两种知识库格式。

⚠️ Windows + 中文路径兼容说明:
  FAISS C++ 的 FileIOWriter 使用 fopen()，在 Windows 上无法处理含中文的路径。
  绕过方案: 序列化/反序列化时使用 Python 原生 open() (完美支持 Unicode)，
  避免让 FAISS C++ 层直接操作文件。
"""
import os
import json
import pickle
import faiss
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from ai.embeddings import get_embedding_model

# FAISS 索引持久化路径
INDEX_PATH = os.path.join(os.path.dirname(__file__), "faiss_index")

# 文件名
INDEX_FILE = "index.faiss"
PKL_FILE = "index.pkl"


def _build_from_md(knowledge_dir: str) -> list[Document]:
    """从 Markdown 文件构建文档列表。"""
    documents = []
    for filename in os.listdir(knowledge_dir):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(knowledge_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        sections = content.split("\n## ")
        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue
            if i == 0 and not section.startswith("# "):
                title = os.path.splitext(filename)[0]
            else:
                lines = section.split("\n", 1)
                title = lines[0].strip()
                section = section if len(lines) == 1 else lines[0] + "\n" + lines[1]

            doc = Document(
                page_content=section[:2000],
                metadata={"source": filename, "title": title},
            )
            documents.append(doc)
    return documents


def _build_from_json(knowledge_dir: str) -> list[Document]:
    """从 JSON 知识库文件构建文档列表。"""
    documents = []
    for filename in os.listdir(knowledge_dir):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(knowledge_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            items = json.load(f)

        for item in items:
            # 拼接可检索的文本内容
            parts = [f"{item.get('name', '')}"]
            if "category" in item:
                parts.append(f"[{item['category']}]")
            parts.append(item.get("description", ""))

            # 附加字段加入检索文本
            for field in ["famous_shops", "tips", "best_viewing", "region", "level"]:
                val = item.get(field, "")
                if val:
                    parts.append(str(val) if isinstance(val, str) else "、".join(val))

            page_content = " ".join(parts)

            doc = Document(
                page_content=page_content[:2000],
                metadata={
                    "source": filename,
                    "name": item.get("name", ""),
                    "category": item.get("category", ""),
                    "type": "food" if "food" in filename else "culture",
                },
            )
            documents.append(doc)
    return documents


def build_knowledge_base(knowledge_dir: str | None = None) -> FAISS:
    """从知识库文件构建 FAISS 向量索引。

    支持格式: .md (Markdown) 和 .json (结构化 JSON)

    ⚠️ 保存时不使用 vector_store.save_local()，因为它调用 FAISS C++
       FileIOWriter → fopen()，在 Windows 上无法处理含中文的路径。
       改用 faiss.serialize_index() + Python open() 写入。
    """
    if knowledge_dir is None:
        knowledge_dir = os.path.join(os.path.dirname(__file__), "knowledge")

    embedding = get_embedding_model()
    documents = _build_from_json(knowledge_dir) + _build_from_md(knowledge_dir)

    if not documents:
        raise RuntimeError(f"知识库目录 {knowledge_dir} 中未找到任何知识文件")

    vector_store = FAISS.from_documents(documents, embedding)

    # 持久化 — 用 Python open() 绕过 FAISS C++ fopen 的 Unicode 路径问题
    os.makedirs(INDEX_PATH, exist_ok=True)
    _save_index_manual(vector_store)

    print(f"[AI] FAISS 索引构建完成，共 {len(documents)} 条知识")
    return vector_store


def load_knowledge_base() -> FAISS | None:
    """加载已有的 FAISS 索引（启动时调用）。
    如果索引不存在，自动从 knowledge/ 目录构建。
    如果 embedding 模型不可用，返回 None（上层降级为纯 LLM 模式）。

    ⚠️ 加载时不使用 FAISS.load_local()，原因同 build_knowledge_base —
       手动读取 + 反序列化以兼容 Windows 中文路径。
    """
    embedding = get_embedding_model()
    if embedding is None:
        print("[AI] Embedding 不可用，跳过 FAISS 知识库加载")
        return None

    try:
        if os.path.exists(os.path.join(INDEX_PATH, INDEX_FILE)):
            return _load_index_manual(embedding)
    except Exception:
        pass

    # 首次启动或索引损坏 → 重建
    try:
        return build_knowledge_base()
    except Exception as e:
        print(f"[AI] FAISS 知识库构建失败: {e}")
        return None


def _save_index_manual(vector_store: FAISS) -> None:
    """手动保存 FAISS 索引，用 Python open() 代替 C++ fopen。

    原因: FAISS C++ FileIOWriter 在 Windows 上无法处理含中文的路径。
    Python 原生 open() 完美支持 Unicode 路径。
    """
    index_path = os.path.join(INDEX_PATH, INDEX_FILE)
    pkl_path = os.path.join(INDEX_PATH, PKL_FILE)

    # 用 faiss.serialize_index 获取字节 → Python write
    index_bytes = faiss.serialize_index(vector_store.index)
    with open(index_path, "wb") as f:
        f.write(index_bytes)

    # docstore + index_to_docstore_id 用 pickle 保存
    with open(pkl_path, "wb") as f:
        pickle.dump(
            (vector_store.docstore, vector_store.index_to_docstore_id), f
        )


def _load_index_manual(embedding) -> FAISS:
    """手动加载 FAISS 索引，用 Python open() 代替 C++ fopen。

    与 _save_index_manual 配对使用，绕过 Windows 中文路径问题。
    """
    index_path = os.path.join(INDEX_PATH, INDEX_FILE)
    pkl_path = os.path.join(INDEX_PATH, PKL_FILE)

    # Python read → faiss.deserialize_index
    with open(index_path, "rb") as f:
        index_bytes = f.read()
    index = faiss.deserialize_index(index_bytes)

    # 恢复 docstore + index_to_docstore_id
    with open(pkl_path, "rb") as f:
        docstore, index_to_docstore_id = pickle.load(f)

    return FAISS(embedding, index, docstore, index_to_docstore_id)
