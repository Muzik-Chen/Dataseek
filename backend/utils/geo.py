"""
地理工具 — Haversine 距离计算 + 潮汕四市坐标。
统一复用，避免在 dashboard.py / hotel.py / route_enricher.py 中重复定义。
"""
import math

# 潮汕四市坐标（用于按经纬度查找最近城市）
CITY_COORDS = {
    "汕头": (23.3541, 116.6822),
    "潮州": (23.6640, 116.6390),
    "揭阳": (23.5480, 116.3700),
    "汕尾": (22.7860, 115.3750),
}


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """计算两点间距离 (km)。"""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearest_city(lat: float, lng: float) -> tuple[str, float]:
    """找到离给定坐标最近的城市，返回 (city_name, distance_km)。"""
    best_city = "汕头"
    best_dist = float("inf")
    for city, (clat, clng) in CITY_COORDS.items():
        d = haversine(lat, lng, clat, clng)
        if d < best_dist:
            best_dist = d
            best_city = city
    return best_city, round(best_dist, 2)
