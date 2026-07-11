"""
向后端 API 插入一条含完整坐标数据的潮汕行程测试数据。
"""
import requests
import json

BASE = "http://localhost:8000/api/v1"

# 先登录
login_resp = requests.post(f"{BASE}/auth/login", json={
    "phone": "13800000001",
    "password": "123456",
})
token = login_resp.json()["data"]["token"]
headers = {"Authorization": f"Bearer {token}"}

# 构建完整的 plan_content（含 geo 坐标）
plan_content = {
    "plans": [
        {
            "plan_id": "A",
            "title": "潮汕三日文化美食之旅",
            "theme": "美食+非遗深度体验",
            "summary": "从汕头老市区出发，途经潮州古城，最终到达揭阳，三天两夜感受潮汕文化的精髓。品牛肉火锅、赏英歌舞、逛古城、喝工夫茶。",
            "transport": {
                "to": {
                    "route": "广州南 → 汕头站 (高铁)",
                    "duration": "约2小时",
                    "cost": 180,
                },
                "return": {
                    "route": "揭阳站 → 广州南 (高铁)",
                    "duration": "约2小时",
                    "cost": 170,
                },
            },
            "hotels": [
                {
                    "name": "汕头国际大酒店",
                    "stars": 4,
                    "price": 350,
                    "level": "high",
                    "reason": "位于市中心，步行可达小公园骑楼群",
                    "lat": 23.3577,
                    "lng": 116.6819,
                },
                {
                    "name": "潮州古城客栈",
                    "stars": 3,
                    "price": 200,
                    "level": "mid",
                    "reason": "古城内的特色民宿，感受最地道的潮州生活",
                    "lat": 23.6656,
                    "lng": 116.6512,
                },
            ],
            "days": [
                {
                    "day": 1,
                    "title": "汕头老城 · 美食探索",
                    "activities": [
                        {
                            "time": "09:00",
                            "name": "小公园骑楼群",
                            "type": "culture",
                            "description": "百年骑楼建筑群，汕头开埠文化的见证",
                            "cost": "免费",
                        },
                        {
                            "time": "11:30",
                            "name": "八合里海记牛肉火锅",
                            "type": "food",
                            "description": "最正宗的潮汕牛肉火锅，现切现涮",
                            "cost": "人均80元",
                        },
                        {
                            "time": "14:00",
                            "name": "南澳岛",
                            "type": "scenery",
                            "description": "广东省唯一海岛县，碧海蓝天",
                            "cost": "免费",
                        },
                        {
                            "time": "18:00",
                            "name": "老妈宫粽球",
                            "type": "food",
                            "description": "百年老字号，潮汕粽球代表",
                            "cost": "人均15元",
                        },
                    ],
                },
                {
                    "day": 2,
                    "title": "潮州古城 · 非遗体验",
                    "activities": [
                        {
                            "time": "08:00",
                            "name": "潮州工夫茶馆",
                            "type": "culture",
                            "description": "体验国家级非遗——潮州工夫茶艺",
                            "cost": "人均50元",
                        },
                        {
                            "time": "10:00",
                            "name": "广济桥 (湘子桥)",
                            "type": "scenery",
                            "description": "中国四大古桥之一，十八梭船廿四洲",
                            "cost": "20元",
                        },
                        {
                            "time": "12:00",
                            "name": "潮州古城牌坊街",
                            "type": "culture",
                            "description": "漫步千年古城，感受潮州历史底蕴",
                            "cost": "免费",
                        },
                        {
                            "time": "14:00",
                            "name": "潮绣展示馆",
                            "type": "culture",
                            "description": "国家级非遗潮绣工艺展示",
                            "cost": "30元",
                        },
                        {
                            "time": "18:00",
                            "name": "潮州鱼生 · 官塘鱼生",
                            "type": "food",
                            "description": "潮州特色鱼生，薄如蝉翼",
                            "cost": "人均60元",
                        },
                    ],
                },
                {
                    "day": 3,
                    "title": "揭阳 · 民俗收官",
                    "activities": [
                        {
                            "time": "09:00",
                            "name": "揭阳学宫",
                            "type": "culture",
                            "description": "岭南地区规模最大的孔庙",
                            "cost": "免费",
                        },
                        {
                            "time": "11:00",
                            "name": "英歌舞表演",
                            "type": "culture",
                            "description": "国家级非遗——普宁英歌舞，气势磅礴",
                            "cost": "50元",
                        },
                        {
                            "time": "13:00",
                            "name": "揭阳蚝烙",
                            "type": "food",
                            "description": "潮汕特色小吃，外酥内嫩",
                            "cost": "人均25元",
                        },
                        {
                            "time": "15:00",
                            "name": "返程",
                            "type": "transport",
                            "description": "揭阳站乘高铁返回广州",
                            "cost": "",
                        },
                    ],
                },
            ],
            "estimated_cost": {
                "transport": 350,
                "hotel": 550,
                "food": 500,
                "tickets": 100,
                "total": 1500,
            },
            "tips": [
                "潮汕地区夏季炎热，注意防晒补水",
                "牛肉火锅建议上午11点前去，午市牛肉最新鲜",
                "古城内很多小巷值得探索，建议穿舒适的鞋",
                "潮汕人爱喝茶，茶馆里可以交到当地朋友",
            ],
            # ── Phase 3 核心：enrichment + route_geo ──
            "enrichment": {
                "weather": [
                    {
                        "city": "汕头",
                        "temperature": 32,
                        "weather_desc": "晴间多云",
                        "humidity": 75,
                        "wind_level": 3,
                        "lat": 23.3577,
                        "lng": 116.6819,
                    },
                    {
                        "city": "潮州",
                        "temperature": 31,
                        "weather_desc": "多云",
                        "humidity": 78,
                        "wind_level": 2,
                        "lat": 23.6656,
                        "lng": 116.6512,
                    },
                    {
                        "city": "揭阳",
                        "temperature": 33,
                        "weather_desc": "晴",
                        "humidity": 70,
                        "wind_level": 3,
                        "lat": 23.5510,
                        "lng": 116.3728,
                    },
                ],
                "foods": [
                    {
                        "food_id": 1,
                        "name": "八合里海记牛肉火锅",
                        "type": "牛肉火锅",
                        "distance_km": 0.5,
                        "price_range": "人均80-120元",
                        "lat": 23.3610,
                        "lng": 116.6890,
                    },
                    {
                        "food_id": 2,
                        "name": "富苑夜糜",
                        "type": "打冷/夜粥",
                        "distance_km": 1.2,
                        "price_range": "人均60-100元",
                        "lat": 23.3550,
                        "lng": 116.6750,
                    },
                    {
                        "food_id": 3,
                        "name": "老妈宫粽球",
                        "type": "小吃",
                        "distance_km": 0.3,
                        "price_range": "人均10-20元",
                        "lat": 23.3590,
                        "lng": 116.6840,
                    },
                    {
                        "food_id": 4,
                        "name": "官塘鱼生",
                        "type": "鱼生",
                        "distance_km": 0.8,
                        "price_range": "人均50-80元",
                        "lat": 23.6680,
                        "lng": 116.6480,
                    },
                    {
                        "food_id": 5,
                        "name": "潮州牛杂",
                        "type": "牛杂",
                        "distance_km": 0.6,
                        "price_range": "人均20-40元",
                        "lat": 23.6630,
                        "lng": 116.6540,
                    },
                    {
                        "food_id": 6,
                        "name": "炒糕粿",
                        "type": "粿类",
                        "distance_km": 1.0,
                        "price_range": "人均15-25元",
                        "lat": 23.3600,
                        "lng": 116.6780,
                    },
                    {
                        "food_id": 7,
                        "name": "揭阳蚝烙",
                        "type": "小吃",
                        "distance_km": 0.4,
                        "price_range": "人均20-35元",
                        "lat": 23.5520,
                        "lng": 116.3700,
                    },
                    {
                        "food_id": 8,
                        "name": "普宁豆干",
                        "type": "小吃",
                        "distance_km": 1.5,
                        "price_range": "人均10-20元",
                        "lat": 23.5490,
                        "lng": 116.3750,
                    },
                ],
                "heritages": [
                    {
                        "id": 1,
                        "name": "潮州工夫茶艺",
                        "category": "传统技艺",
                        "type": "国家级非遗",
                        "distance_km": 0.5,
                        "lat": 23.6670,
                        "lng": 116.6500,
                    },
                    {
                        "id": 2,
                        "name": "普宁英歌舞",
                        "category": "传统舞蹈",
                        "type": "国家级非遗",
                        "distance_km": 0.3,
                        "lat": 23.5530,
                        "lng": 116.3680,
                    },
                    {
                        "id": 3,
                        "name": "潮绣",
                        "category": "传统美术",
                        "type": "国家级非遗",
                        "distance_km": 0.6,
                        "lat": 23.6640,
                        "lng": 116.6530,
                    },
                    {
                        "id": 4,
                        "name": "潮剧",
                        "category": "传统戏剧",
                        "type": "国家级非遗",
                        "distance_km": 0.8,
                        "lat": 23.3580,
                        "lng": 116.6820,
                    },
                    {
                        "id": 5,
                        "name": "潮州木雕",
                        "category": "传统美术",
                        "type": "国家级非遗",
                        "distance_km": 1.0,
                        "lat": 23.6660,
                        "lng": 116.6490,
                    },
                    {
                        "id": 6,
                        "name": "嵌瓷",
                        "category": "传统技艺",
                        "type": "国家级非遗",
                        "distance_km": 1.2,
                        "lat": 23.6650,
                        "lng": 116.6520,
                    },
                ],
                "hotels": [
                    {
                        "id": 1,
                        "name": "汕头国际大酒店",
                        "stars": 4,
                        "price_min": 320,
                        "price_max": 450,
                        "distance_km": 0.2,
                        "lat": 23.3577,
                        "lng": 116.6819,
                    },
                    {
                        "id": 2,
                        "name": "汕头君华海逸酒店",
                        "stars": 5,
                        "price_min": 550,
                        "price_max": 800,
                        "distance_km": 1.0,
                        "lat": 23.3530,
                        "lng": 116.6900,
                    },
                    {
                        "id": 3,
                        "name": "潮州古城客栈",
                        "stars": 3,
                        "price_min": 180,
                        "price_max": 280,
                        "distance_km": 0.3,
                        "lat": 23.6656,
                        "lng": 116.6512,
                    },
                    {
                        "id": 4,
                        "name": "潮州迎宾馆",
                        "stars": 4,
                        "price_min": 350,
                        "price_max": 500,
                        "distance_km": 1.5,
                        "lat": 23.6600,
                        "lng": 116.6450,
                    },
                ],
                "crowd": [
                    {
                        "location_name": "小公园骑楼",
                        "crowd_level": "高",
                        "estimated_count": 3500,
                        "distance_km": 0.1,
                        "lat": 23.3590,
                        "lng": 116.6830,
                    },
                    {
                        "location_name": "广济桥",
                        "crowd_level": "高",
                        "estimated_count": 4200,
                        "distance_km": 0.2,
                        "lat": 23.6670,
                        "lng": 116.6540,
                    },
                    {
                        "location_name": "牌坊街",
                        "crowd_level": "中",
                        "estimated_count": 2800,
                        "distance_km": 0.3,
                        "lat": 23.6645,
                        "lng": 116.6505,
                    },
                    {
                        "location_name": "南澳岛",
                        "crowd_level": "中",
                        "estimated_count": 2100,
                        "distance_km": 0.5,
                        "lat": 23.4230,
                        "lng": 117.0280,
                    },
                    {
                        "location_name": "揭阳学宫",
                        "crowd_level": "低",
                        "estimated_count": 600,
                        "distance_km": 0.1,
                        "lat": 23.5515,
                        "lng": 116.3730,
                    },
                ],
                "interest_matches": [
                    {
                        "hint": "美食",
                        "items": ["八合里海记牛肉火锅", "官塘鱼生", "富苑夜糜"],
                    },
                    {
                        "hint": "非遗",
                        "items": ["工夫茶", "英歌舞", "潮绣"],
                    },
                ],
            },
            "route_geo": {
                "waypoints": [
                    {"name": "汕头站", "lat": 23.3700, "lng": 116.7400, "source": "geocoded"},
                    {"name": "小公园骑楼群", "lat": 23.3590, "lng": 116.6830, "source": "geocoded"},
                    {"name": "南澳岛", "lat": 23.4230, "lng": 117.0280, "source": "geocoded"},
                    {"name": "潮州古城", "lat": 23.6656, "lng": 116.6512, "source": "geocoded"},
                    {"name": "广济桥", "lat": 23.6670, "lng": 116.6540, "source": "geocoded"},
                    {"name": "揭阳学宫", "lat": 23.5515, "lng": 116.3730, "source": "geocoded"},
                    {"name": "揭阳站", "lat": 23.5700, "lng": 116.4000, "source": "geocoded"},
                ],
                "route_line": [
                    [116.7400, 23.3700],
                    [116.6830, 23.3590],
                    [117.0280, 23.4230],
                    [116.6512, 23.6656],
                    [116.6540, 23.6670],
                    [116.3730, 23.5515],
                    [116.4000, 23.5700],
                ],
            },
        },
    ],
}

# 调用 import 接口
payload = {
    "title": "潮汕三日文化美食之旅",
    "days": 3,
    "crowd_type": "solo",
    "preferences": ["美食", "非遗", "自然风光"],
    "plan_content": plan_content,
}

resp = requests.post(
    f"{BASE}/trip/plan/import",
    headers=headers,
    json=payload,
)

print(f"Status: {resp.status_code}")
print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
