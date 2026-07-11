"""
JWT 生成/校验 + 密码哈希 + 验证码生成。
"""
import random
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from config import get_settings

settings = get_settings()


# --- 密码 ---
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# --- JWT ---
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


# --- 验证码 ---
def generate_sms_code(length: int = 6) -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


# --- 工具 ---
def mask_phone(phone: str) -> str:
    """手机号脱敏：138****8000（保留以兼容旧代码）"""
    return phone[:3] + "****" + phone[-4:] if len(phone) == 11 else phone


def mask_email(email: str) -> str:
    """邮箱脱敏：t***@qq.com"""
    if "@" not in email:
        return email
    prefix, domain = email.split("@", 1)
    masked_prefix = prefix[0] + "***" if len(prefix) > 1 else prefix
    return f"{masked_prefix}@{domain}"
