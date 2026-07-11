"""
美食推荐服务 — 基于用户偏好和协同过滤的推荐引擎。

当前为基于规则的占位实现，后续可替换为：
- 基于 LLM 的语义推荐（通过 LangChain 调用大模型分析偏好）
- 基于协同过滤的推荐（用户行为数据积累后）
- 混合推荐（规则 + LLM + 协同过滤加权融合）
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.food import Food, FoodCategory


class FoodRecommendService:
    """美食推荐服务。"""

    # 偏好关键词 → 推荐策略映射
    PREFERENCE_RULES = {
        "辣": {"tags": ["辣", "川味"]},
        "清淡": {"tags": ["清淡", "原味", "清蒸"]},
        "海鲜": {"tags": ["海鲜", "鱼", "虾", "蟹", "贝"]},
        "小吃": {"type": "dish", "tags": ["小吃", "粿", "肠粉"]},
        "正餐": {"type": "shop", "tags": ["火锅", "大排档", "酒楼"]},
        "甜品": {"tags": ["甜汤", "糖水", "甜点", "饼"]},
        "牛肉": {"tags": ["牛肉", "牛"]},
        "粿": {"tags": ["粿", "米制品"]},
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def recommend(
        self,
        preference: str,
        limit: int = 6,
    ) -> list[dict]:
        """根据偏好文本推荐美食。

        Args:
            preference: 用户输入的偏好描述
            limit: 返回结果数量上限

        Returns:
            推荐结果列表，每项包含 food 信息和推荐理由
        """
        # 1. 规则匹配
        rule = self._match_rule(preference)

        # 2. 构建查询
        q = select(Food)

        if rule:
            if "type" in rule:
                q = q.where(Food.type == rule["type"])
            # tags 匹配（JSON 字段）
            # 简化处理：先用 is_recommended 作为候选池
            q = q.where(Food.is_recommended == True)

        q = q.order_by(Food.view_count.desc()).limit(limit * 2)
        rows = (await self.db.execute(q)).scalars().all()

        # 如果没有推荐菜，回退到热门
        if not rows:
            q = select(Food).order_by(Food.view_count.desc()).limit(limit * 2)
            rows = (await self.db.execute(q)).scalars().all()

        # 3. 获取分类名称
        cat_ids = {r.category_id for r in rows}
        cats = (await self.db.execute(
            select(FoodCategory).where(FoodCategory.id.in_(cat_ids))
        )).scalars().all()
        cat_map = {c.id: c.name for c in cats}

        # 4. 构建结果（简单打分排序）
        results = []
        for r in rows[:limit]:
            score = self._calculate_score(r, preference)
            results.append({
                "food_id": r.id,
                "name": r.name,
                "category_name": cat_map.get(r.category_id, ""),
                "type": r.type,
                "reason": self._generate_reason(r, cat_map),
                "score": round(score, 2),
                "image_url": r.image_url,
                "price_range": r.price_range,
            })

        # 按分数降序
        results.sort(key=lambda x: x["score"], reverse=True)

        return results

    def _match_rule(self, preference: str) -> dict | None:
        """匹配偏好规则。"""
        for keyword, rule in self.PREFERENCE_RULES.items():
            if keyword in preference:
                return rule
        return None

    def _calculate_score(self, food: Food, preference: str) -> float:
        """计算推荐分数（占位：简单加权）。"""
        score = 0.5  # 基础分
        if food.is_recommended:
            score += 0.2
        if food.view_count:
            score += min(food.view_count / 1000, 0.3)  # 浏览量加权，上限 0.3
        # 关键词匹配加分
        if preference and food.name:
            for char in preference:
                if char in food.name:
                    score += 0.05
        return min(score, 1.0)

    def _generate_reason(self, food: Food, cat_map: dict) -> str:
        """生成推荐理由。"""
        cat_name = cat_map.get(food.category_id, "")
        if food.is_recommended:
            return f"🔥 热门推荐 — {cat_name}"
        if food.view_count and food.view_count > 100:
            return f"👀 高人气 — {cat_name}"
        return f"🍽️ {cat_name}精选"
