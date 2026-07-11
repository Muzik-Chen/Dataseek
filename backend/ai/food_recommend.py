"""
美食推荐 Chain — 用户输入偏好 → LLM 理解意图 + 匹配数据库 → 推荐结果。

流程：
1. 从 MySQL 取 Top-50 热门美食作为候选池
2. LLM 基于用户偏好从候选池中筛选 Top-5
3. 返回结构化推荐结果（含理由和评分）
"""
import json
from pydantic import BaseModel

from langchain_core.output_parsers import JsonOutputParser

from ai.llm import get_llm
from ai.prompts import RECOMMEND_PROMPT


class FoodRecommendation(BaseModel):
    food_id: int
    name: str
    reason: str
    score: float


class RecommendResult(BaseModel):
    recommendations: list[FoodRecommendation]
    summary: str


# RECOMMEND_PROMPT 已迁移至 ai.prompts.recommend；通过 from ai.prompts import RECOMMEND_PROMPT 导入


async def recommend_foods(
    user_preference: str,
    foods_from_db: list[dict],
    temperature: float = 0.7,
) -> dict:
    """AI 美食推荐。

    Args:
        user_preference: 用户自然语言偏好（如"想吃牛肉火锅，人均100以内"）
        foods_from_db: 从 MySQL 查出的候选美食列表（建议 Top-50）
        temperature: LLM 温度

    Returns:
        {"recommendations": [...], "summary": "..."}
    """
    parser = JsonOutputParser(pydantic_object=RecommendResult)
    llm = get_llm(temperature=temperature, streaming=False)

    # 候选列表精简字段送给 LLM
    candidates_str = json.dumps(
        [
            {
                "food_id": f.get("food_id", f.get("id")),
                "name": f["name"],
                "type": f.get("type", ""),
                "category": f.get("category_name", ""),
                "price_range": f.get("price_range", ""),
                "tags": f.get("tags", []),
            }
            for f in foods_from_db
        ],
        ensure_ascii=False,
        indent=2,
    )

    chain = RECOMMEND_PROMPT | llm | parser

    result = await chain.ainvoke({
        "candidates": candidates_str,
        "preference": user_preference,
        "format_instructions": parser.get_format_instructions(),
    })

    # 规范化返回值：LangChain JsonOutputParser 可能返回 Pydantic 对象、dict 或 list
    if isinstance(result, RecommendResult):
        return result.model_dump()
    elif isinstance(result, dict):
        return result
    elif isinstance(result, list):
        # LangChain 某些版本会解包 Pydantic model，直接返回 recommendations 列表
        return {"recommendations": result, "summary": f"根据您的偏好，为您推荐 {len(result)} 个美食选择。"}
    else:
        return {"recommendations": [], "summary": "推荐系统暂不可用，请稍后重试。"}


async def recommend_foods_rule_based(
    user_preference: str,
    foods_from_db: list[dict],
) -> dict:
    """基于规则的推荐（LLM 不可用时的降级方案）。

    按关键词匹配 + 推荐标记 + 浏览数排序。
    """
    results = []
    pref_lower = user_preference.lower()

    for food in foods_from_db:
        score = 0.5
        reason_parts = []

        # 关键词匹配
        name = food.get("name", "")
        tags = food.get("tags", [])
        cat = food.get("category_name", "")

        if any(kw in user_preference for kw in [name, cat] + (tags if isinstance(tags, list) else [])):
            score += 0.3
            reason_parts.append("匹配您的偏好")

        if food.get("is_recommended"):
            score += 0.15
            reason_parts.append("热门推荐")

        view_count = food.get("view_count", 0)
        if view_count > 100:
            score += min(view_count / 2000, 0.15)

        # 价格匹配
        price = food.get("price_range", "")
        if "便宜" in pref_lower or "实惠" in pref_lower:
            if price in ("¥", "¥¥"):
                score += 0.1
        elif "贵" not in pref_lower and "高端" not in pref_lower:
            if price in ("¥¥", "¥¥¥"):
                score += 0.05

        if score > 0.5 or food.get("is_recommended"):
            results.append({
                "food_id": food.get("food_id", food.get("id")),
                "name": name,
                "reason": "；".join(reason_parts) if reason_parts else f"{cat}精选推荐",
                "score": round(min(score, 1.0), 2),
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:5]

    return {
        "recommendations": results,
        "summary": f"根据您的偏好，为您推荐 {len(results)} 个美食选择。" if results else "暂未找到完全匹配的美食，请尝试调整偏好描述。",
    }
