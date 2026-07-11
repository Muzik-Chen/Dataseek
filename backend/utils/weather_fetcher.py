"""
气象数据拉取 + 人流模拟数据生成 + SMS 清理定时任务。
"""
import os
import random
import httpx
from datetime import datetime, timedelta
from sqlalchemy import text

from database import async_session_factory


# === 气象数据拉取（和风天气 API）===

QWEATHER_API_KEY = os.getenv("QWEATHER_API_KEY", "")
QWEATHER_BASE = "https://devapi.qweather.com/v7"

# 潮汕四市 城市 ID（和风天气）
CITY_IDS = {
    "汕头": "101280501",
    "潮州": "101280801",
    "揭阳": "101281101",
    "汕尾": "101281301",
}

WEATHER_DESC_MAP = {
    "100": "晴", "101": "多云", "102": "少云", "103": "晴间多云",
    "104": "阴", "300": "阵雨", "301": "强阵雨", "302": "雷阵雨",
    "303": "强雷阵雨", "304": "雷阵雨伴有冰雹", "305": "小雨", "306": "中雨",
    "307": "大雨", "308": "暴雨", "309": "大暴雨", "310": "特大暴雨",
    "400": "小雪", "401": "中雪", "402": "大雪", "500": "雾", "501": "雾霾",
}


async def fetch_weather_data():
    """
    从和风天气 API 拉取潮汕四市实时气象数据，写入 weather_records 表。
    如果 API Key 未配置，使用模拟数据。
    """
    async with async_session_factory() as db:
        record_time = datetime.now().replace(minute=0, second=0, microsecond=0)

        # 方案 A：有 API Key → 真实拉取
        if QWEATHER_API_KEY and QWEATHER_API_KEY != "your_key_here":
            await _fetch_real_weather(db, record_time)
        else:
            # 方案 B：无 API Key → 模拟数据（演示用）
            await _generate_mock_weather(db, record_time)

        # 清理 7 天前的旧气象数据
        cutoff = record_time - timedelta(days=7)
        await db.execute(
            text("DELETE FROM weather_records WHERE record_time < :cutoff"),
            {"cutoff": cutoff},
        )

        await db.commit()


async def _fetch_real_weather(db, record_time: datetime):
    """调用和风天气实时 API。"""
    async with httpx.AsyncClient(timeout=10) as client:
        for region, city_id in CITY_IDS.items():
            try:
                resp = await client.get(
                    f"{QWEATHER_BASE}/weather/now",
                    params={"location": city_id, "key": QWEATHER_API_KEY},
                )
                data = resp.json()
                if data.get("code") == "200":
                    now = data["now"]
                    await db.execute(
                        text(
                            "INSERT INTO weather_records (region, temperature, humidity, weather_desc, wind_level, record_time) "
                            "VALUES (:region, :temp, :humidity, :desc, :wind, :time)"
                        ),
                        {
                            "region": region,
                            "temp": float(now.get("temp", 25)),
                            "humidity": int(now.get("humidity", 70)),
                            "desc": WEATHER_DESC_MAP.get(now.get("icon", "100"), now.get("text", "多云")),
                            "wind": int(now.get("windScale", 2)),
                            "time": record_time,
                        },
                    )
                else:
                    # API 报错 → 该城市用模拟数据
                    await _insert_mock_weather_row(db, region, record_time)
            except Exception:
                await _insert_mock_weather_row(db, region, record_time)


async def _generate_mock_weather(db, record_time: datetime):
    """为所有四市填充 24 小时模拟气象数据。"""
    for region in CITY_IDS:
        for hour_offset in range(24):
            t = record_time - timedelta(hours=hour_offset)
            await _insert_mock_weather_row(db, region, t)


async def _insert_mock_weather_row(db, region: str, record_time: datetime):
    """插入一条模拟气象数据。"""
    base_temp = {"汕头": 29, "潮州": 28, "揭阳": 28, "汕尾": 30}.get(region, 28)
    # 凌晨温度低，午后高
    hour = record_time.hour
    temp_variation = -3 if hour < 6 else (2 if 12 <= hour <= 15 else 0)
    temp = round(base_temp + temp_variation + random.uniform(-1.5, 1.5), 1)
    humidity = random.randint(55, 90)
    weather_desc = random.choice(
        ["晴", "晴", "晴", "多云", "多云", "多云", "阴", "小雨"]
    )
    wind_level = random.randint(0, 4)
    await db.execute(
        text(
            "INSERT INTO weather_records (region, temperature, humidity, weather_desc, wind_level, record_time) "
            "VALUES (:region, :temp, :humidity, :desc, :wind, :time)"
        ),
        {
            "region": region,
            "temp": temp,
            "humidity": humidity,
            "desc": weather_desc,
            "wind": wind_level,
            "time": record_time,
        },
    )


# === 人流模拟数据生成 ===

# 硬编码回退列表 — 当 crowd_locations 表为空时使用
CROWD_LOCATIONS_FALLBACK = {
    "汕头": ["小公园", "南澳岛", "八合里海记(总店)", "汕头市博物馆", "广场轮渡", "西堤公园"],
    "潮州": ["广济桥", "牌坊街", "开元寺", "韩文公祠", "龙湖古寨"],
    "揭阳": ["揭阳学宫", "城隍庙", "进贤门", "黄岐山"],
    "汕尾": ["凤山妈祖", "红海湾", "玄武山"],
}

# 不同时段的人流基数
HOUR_FACTORS = {
    6: 0.2, 7: 0.3, 8: 0.5, 9: 0.7, 10: 0.85, 11: 0.9,
    12: 0.7, 13: 0.6, 14: 0.75, 15: 0.8, 16: 0.85, 17: 0.75,
    18: 0.5, 19: 0.4, 20: 0.3, 21: 0.15, 22: 0.05, 23: 0.02,
    0: 0.01, 1: 0.01, 2: 0.01, 3: 0.01, 4: 0.01, 5: 0.02,
}


async def _load_crowd_locations(db) -> list[dict]:
    """
    从 crowd_locations 表读取监测点列表。
    返回 [{"location_name": str, "region": str, "base_capacity": int}, ...]。
    若表为空则回退到硬编码列表。
    """
    from sqlalchemy import select
    from models.dashboard import CrowdLocation

    rows = (await db.execute(select(CrowdLocation))).scalars().all()
    if rows:
        return [
            {
                "location_name": r.location_name,
                "region": r.region,
                "base_capacity": r.base_capacity,
            }
            for r in rows
        ]

    # 回退：用硬编码字典
    fallback = []
    for region, locations in CROWD_LOCATIONS_FALLBACK.items():
        for loc in locations:
            # 从旧字典中取 base_capacity
            base = _get_base_capacity(loc)
            fallback.append({
                "location_name": loc,
                "region": region,
                "base_capacity": base[1],  # (min, max) → 取 max
            })
    return fallback


def _get_base_capacity(location: str) -> tuple[int, int]:
    """按地点名返回 (min, max) 基准容量。"""
    return {
        "小公园": (500, 8000), "南澳岛": (1000, 15000),
        "八合里海记(总店)": (50, 500), "汕头市博物馆": (200, 2000),
        "广场轮渡": (100, 2000), "西堤公园": (200, 3000),
        "广济桥": (500, 6000), "牌坊街": (800, 10000),
        "开元寺": (300, 3000), "韩文公祠": (100, 1500),
        "龙湖古寨": (100, 2000), "揭阳学宫": (200, 1500),
        "城隍庙": (100, 1000), "进贤门": (100, 1200),
        "黄岐山": (100, 2000), "凤山妈祖": (300, 3000),
        "红海湾": (500, 8000), "玄武山": (200, 2000),
    }.get(location, (100, 1000))


async def generate_crowd_data():
    """
    为潮汕四市热门景点生成当前时段人流模拟数据，写入 crowd_records 表。
    优先从 crowd_locations 表读取监测点（含坐标+容量），
    若表为空则回退到硬编码列表。
    """
    async with async_session_factory() as db:
        now = datetime.now()
        record_time = now.replace(minute=0, second=0, microsecond=0)
        hour = now.hour

        locations = await _load_crowd_locations(db)

        for loc in locations:
            base_max = loc["base_capacity"]
            base_min = max(base_max // 10, 50)  # min ≈ max/10

            factor = HOUR_FACTORS.get(hour, 0.3)
            fluctuation = random.uniform(0.8, 1.2)
            estimated_count = int(base_min + (base_max - base_min) * factor * fluctuation)

            # 根据预估人数映射人流等级 1-5
            if estimated_count < 500:
                crowd_level = 1
            elif estimated_count < 1500:
                crowd_level = 2
            elif estimated_count < 3500:
                crowd_level = 3
            elif estimated_count < 6000:
                crowd_level = 4
            else:
                crowd_level = 5

            await db.execute(
                text(
                    "INSERT INTO crowd_records (region, location_name, crowd_level, estimated_count, record_time) "
                    "VALUES (:region, :location, :level, :count, :time)"
                ),
                {
                    "region": loc["region"],
                    "location": loc["location_name"],
                    "level": crowd_level,
                    "count": estimated_count,
                    "time": record_time,
                },
            )

        # 清理 7 天前的旧人流数据
        cutoff = record_time - timedelta(days=7)
        await db.execute(
            text("DELETE FROM crowd_records WHERE record_time < :cutoff"),
            {"cutoff": cutoff},
        )

        await db.commit()


# === SMS 验证码清理 ===

async def cleanup_expired_sms():
    """清理过期的短信验证码记录（保留最近 1 小时）。"""
    async with async_session_factory() as db:
        cutoff = datetime.now() - timedelta(hours=1)
        await db.execute(
            text("DELETE FROM sms_codes WHERE expires_at < :cutoff"),
            {"cutoff": cutoff},
        )
        # 也清理旧的登录尝试记录
        await db.execute(
            text("DELETE FROM login_attempts WHERE created_at < :cutoff"),
            {"cutoff": cutoff},
        )
        await db.commit()


# === 定时任务注册辅助 ===

def register_scheduler_jobs(scheduler):
    """向 APScheduler 注册所有定时任务。"""
    try:
        # 每小时拉取气象数据
        scheduler.add_job(
            fetch_weather_data,
            "interval",
            hours=1,
            id="fetch_weather",
            replace_existing=True,
        )
        # 每小时生成人流模拟数据
        scheduler.add_job(
            generate_crowd_data,
            "interval",
            hours=1,
            id="generate_crowd",
            replace_existing=True,
        )
        # 每小时清理过期 SMS 和登录尝试记录
        scheduler.add_job(
            cleanup_expired_sms,
            "interval",
            hours=1,
            id="cleanup_sms",
            replace_existing=True,
        )
        print("[Scheduler] 定时任务注册完成: 气象拉取 + 人流模拟 + SMS清理")
    except Exception as e:
        print(f"[Scheduler] 定时任务注册失败: {e}")
