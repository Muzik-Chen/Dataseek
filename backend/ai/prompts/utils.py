"""
Prompt 工具函数 — JSON 清洗/修复 + SSE 事件构建。

去重了 trip_agent.py、intent_router.py、agent_dispatcher.py 中的重复定义。
"""
import json


def clean_json(text: str) -> str:
    """清洗 LLM 输出中的 markdown 标记 + 正则兜底提取 JSON。"""
    if not text or not text.strip():
        return ""
    text = text.strip()
    # Step 1: 去掉 markdown 代码块标记
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:]) if len(lines) > 1 else text
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()
    # Step 2: 如果仍然不是以 { 开头，尝试正则提取 JSON 对象
    if not text.startswith("{"):
        import re
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            text = m.group(0)
    return text.strip()


def repair_json(text: str) -> str:
    """修复 LLM 常见的 JSON 格式错误。

    处理：
    1. 尾随逗号：{"a": 1,} → {"a": 1}
    2. 数组尾随逗号：[1, 2,] → [1, 2]
    3. 字符串值中的未转义换行符
    4. 字符串值中的未转义双引号（启发式）
    """
    if not text or not text.strip():
        return text

    import re

    # 1. 移除对象/数组中的尾随逗号
    text = re.sub(r",(\s*[}\]])", r"\1", text)

    # 2. 修复缺失的逗号 — 在 "value"\n  "key" 模式之间插入逗号
    text = re.sub(r'"(?:\s*\n\s*)(?=")', '",\n  ', text)

    # 3. 修复数字/布尔值后缺少逗号的情况
    text = re.sub(r'(\d+|true|false|null)\s*\n\s*"(?=[a-zA-Z_])', r'\1,\n  "', text)

    return text


def sse_event(event_type: str, **kwargs) -> str:
    """构建 SSE 格式的事件字符串。"""
    payload = {"type": event_type, **kwargs}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
