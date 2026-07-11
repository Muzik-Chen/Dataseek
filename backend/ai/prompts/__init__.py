"""
Prompt 模板 — 各 AI 场景的 System/User Prompt 定义。
"""
from .chat import SYSTEM_PROMPT as CHAT_SYSTEM_PROMPT
from .recommend import RECOMMEND_PROMPT
from .trip import PLAN_PROMPT, NARRATOR_PROMPT, PLAN_THEMES
from .intent import ROUTER_PROMPT, INTENT_SCHEMA
from .refine import REFINE_PROMPT
from .utils import clean_json, repair_json, sse_event

__all__ = [
    # chat
    "CHAT_SYSTEM_PROMPT",
    # recommend
    "RECOMMEND_PROMPT",
    # trip
    "PLAN_PROMPT", "NARRATOR_PROMPT", "PLAN_THEMES",
    # intent
    "ROUTER_PROMPT", "INTENT_SCHEMA",
    # refine
    "REFINE_PROMPT",
    # utils
    "clean_json", "repair_json", "sse_event",
]
