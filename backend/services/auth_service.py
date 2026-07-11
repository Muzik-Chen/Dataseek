"""
认证业务逻辑 — 注册/登录/验证码/密码重置（邮箱版）。
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, SmsCode, LoginAttempt
from utils.security import (
    hash_password, verify_password,
    create_access_token, generate_sms_code, mask_email,
)
from utils.email_sender import send_verification_code


# --- 验证码 ---

async def send_sms_code(
    db: AsyncSession, email: str, purpose: str = "register",
) -> tuple[str, int]:
    """发送邮箱验证码。成功返回 (code, expire_seconds)，失败 raise ValueError。"""
    # 频率检查 — 60 秒内仅 1 次
    now = datetime.now(timezone.utc)
    recent = (await db.execute(
        select(SmsCode).where(
            SmsCode.phone == email,
            SmsCode.created_at > now - timedelta(seconds=60),
        )
    )).scalar()
    if recent:
        raise ValueError("请60秒后再试")

    # 频率检查 — 每小时最多 5 次
    one_hour_ago = now - timedelta(hours=1)
    hourly_count = (await db.execute(
        select(func.count(SmsCode.id)).where(
            SmsCode.phone == email,
            SmsCode.created_at > one_hour_ago,
        )
    )).scalar()
    if hourly_count and hourly_count >= 5:
        raise ValueError("发送频率过高，请稍后再试")

    code = generate_sms_code()

    # 真实发送
    if not send_verification_code(email, code):
        raise ValueError("邮件发送失败，请稍后再试")

    expires_at = now + timedelta(minutes=5)
    sms = SmsCode(phone=email, code=code, purpose=purpose, expires_at=expires_at)
    db.add(sms)
    await db.flush()

    print(f"[EMAIL] {email} 验证码: {code}")
    return code, 300


async def verify_sms_code(
    db: AsyncSession, email: str, code: str, purpose: str,
) -> SmsCode:
    """校验验证码并标记已使用。不合法时 raise ValueError。"""
    sms = (await db.execute(
        select(SmsCode).where(
            SmsCode.phone == email,
            SmsCode.code == code,
            SmsCode.purpose == purpose,
            SmsCode.used == False,
            SmsCode.expires_at > datetime.now(timezone.utc),
        ).order_by(SmsCode.created_at.desc())
    )).scalar()
    if not sms:
        raise ValueError("验证码错误或已过期")
    sms.used = True
    return sms


# --- 用户注册/登录 ---

async def register_user(
    db: AsyncSession,
    email: str, code: str, password: str, confirm_password: str, nickname: str,
) -> tuple[User, str]:
    """注册新用户。返回 (user, jwt_token)。"""
    # 检查邮箱
    existing = (await db.execute(
        select(User).where(User.email == email)
    )).scalar()
    if existing:
        raise ValueError("该邮箱已注册")

    # 密码二次验证
    if password != confirm_password:
        raise ValueError("两次输入的密码不一致")

    await verify_sms_code(db, email, code, purpose="register")

    user = User(
        email=email,
        password_hash=hash_password(password),
        nickname=nickname or email.split("@")[0],
    )
    db.add(user)
    await db.flush()

    token = create_access_token({"user_id": user.id, "role": user.role})
    return user, token


async def login_user(
    db: AsyncSession, email: str, password: str, client_ip: str = "",
) -> tuple[User, str]:
    """登录。检查锁定、校验密码、记录登录尝试。返回 (user, jwt_token)。"""
    # 检查锁定
    fifteen_min_ago = datetime.now(timezone.utc) - timedelta(minutes=15)
    failed_count = (await db.execute(
        select(func.count(LoginAttempt.id)).where(
            LoginAttempt.phone == email,
            LoginAttempt.success == False,
            LoginAttempt.created_at > fifteen_min_ago,
        )
    )).scalar()
    if failed_count and failed_count >= 5:
        raise PermissionError("账号已临时锁定，请15分钟后再试")

    user = (await db.execute(
        select(User).where(User.email == email)
    )).scalar()
    if not user or not verify_password(password, user.password_hash):
        # 记录失败
        db.add(LoginAttempt(phone=email, ip_address=client_ip, success=False))
        await db.flush()
        raise ValueError("邮箱或密码错误")

    if user.is_disabled:
        raise PermissionError("账号已被禁用")

    # 记录成功
    db.add(LoginAttempt(phone=email, ip_address=client_ip, success=True))
    await db.flush()

    token = create_access_token({"user_id": user.id, "role": user.role})
    return user, token


async def reset_password(
    db: AsyncSession, email: str, code: str, new_password: str,
) -> None:
    """忘记密码 — 验证邮箱验证码后重置密码。"""
    user = (await db.execute(
        select(User).where(User.email == email)
    )).scalar()
    if not user:
        raise ValueError("该邮箱未注册")

    await verify_sms_code(db, email, code, purpose="reset_password")
    user.password_hash = hash_password(new_password)
    await db.flush()


def logout_user() -> None:
    """JWT 无状态登出 — 客户端删除 token 即可。"""
    pass
