"""
业务逻辑层 — 供 routers 调用，封装复杂业务流程。

使用方式:
    from services.auth_service import register_user, login_user
    from services.food_service import list_foods, get_food_detail
    from services.trip_service import create_trip_plan
    from services.community_service import list_posts, toggle_like
"""
from .recommend import FoodRecommendService
from .chatbot import ChatbotService

__all__ = [
    "FoodRecommendService",
    "ChatbotService",
]
