"""
认证路由 — 邮箱注册/登录/验证码（163 SMTP 真实发送）。
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User, SmsCode, LoginAttempt
from schemas.auth import (
    SendCodeRequest, RegisterRequest, LoginRequest,
    ResetPasswordRequest, AuthOut,
)
from utils.security import (
    hash_password, verify_password,
    create_access_token, generate_sms_code, mask_email,
)
from utils.email_sender import send_verification_code
from utils.response import success
from utils.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


def _user_dict(user: User) -> dict:
    """构建返回给前端的用户信息字典。"""
    return {
        "id": user.id,
        "email": mask_email(user.email),
        "phone": user.phone,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "persona_type": user.persona_type,
<<<<<<< HEAD
        "role": user.role,
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
    }


@router.post("/send-code")
async def send_code(req: SendCodeRequest, db: AsyncSession = Depends(get_db)):
    """发送邮箱验证码 — 通过 163 SMTP 真实发送。"""
    # 校验邮箱格式
    email = req.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[1]:
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    # 频率检查 — 60 秒内仅 1 次
    now = datetime.now(timezone.utc)
    recent = (await db.execute(
        select(SmsCode).where(
            SmsCode.phone == email,
            SmsCode.created_at > now - timedelta(seconds=60),
        )
    )).scalar()
    if recent:
        raise HTTPException(status_code=429, detail="请60秒后再试")

    # 频率检查 — 每小时最多 5 次
    one_hour_ago = now - timedelta(hours=1)
    hourly_count = (await db.execute(
        select(func.count(SmsCode.id)).where(
            SmsCode.phone == email,
            SmsCode.created_at > one_hour_ago,
        )
    )).scalar()
    if hourly_count and hourly_count >= 5:
        raise HTTPException(status_code=429, detail="发送频率过高，请稍后再试")

    # 如果是注册，检查邮箱是否已注册
    if req.purpose == "register":
        existing = (await db.execute(
            select(User).where(User.email == email)
        )).scalar()
        if existing:
            raise HTTPException(status_code=400, detail="该邮箱已注册")

    # 先生成验证码并尝试发送邮件，成功后再入库
    code = generate_sms_code()

    # 真实发送邮件
    if not send_verification_code(email, code):
        raise HTTPException(status_code=500, detail="邮件发送失败，请稍后再试")

    expires_at = now + timedelta(minutes=5)
    sms = SmsCode(phone=email, code=code, purpose=req.purpose, expires_at=expires_at)
    db.add(sms)
    await db.flush()

    print(f"[EMAIL] {email} 验证码: {code}")
    return success({"expire_seconds": 300}, "验证码已发送")


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """邮箱注册。"""
    email = req.email.strip().lower()

    # 校验邮箱是否已注册
    existing = (await db.execute(
        select(User).where(User.email == email)
    )).scalar()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已注册")

    # 密码二次验证
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")

    # 校验验证码
    sms = (await db.execute(
        select(SmsCode).where(
            SmsCode.phone == email,
            SmsCode.code == req.code,
            SmsCode.purpose == "register",
            SmsCode.used == False,
            SmsCode.expires_at > datetime.now(timezone.utc),
        ).order_by(SmsCode.created_at.desc())
    )).scalar()
    if not sms:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    sms.used = True

    user = User(
        email=email,
        password_hash=hash_password(req.password),
        nickname=req.nickname or email.split("@")[0],
    )
    db.add(user)
    await db.flush()

    token = create_access_token({"user_id": user.id, "role": user.role})
    return success({
        "token": token,
        "user": _user_dict(user),
    })


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """邮箱 + 密码登录。"""
    email = req.email.strip().lower()

    # 检查锁定 — 15 分钟内同一邮箱最多 5 次失败
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
    fail_count = (await db.execute(
        select(func.count(LoginAttempt.id)).where(
            LoginAttempt.phone == email,
            LoginAttempt.success == False,
            LoginAttempt.created_at > cutoff,
        )
    )).scalar()
    if fail_count and fail_count >= 5:
        raise HTTPException(status_code=429, detail="账号已临时锁定，请15分钟后再试")

    user = (await db.execute(
        select(User).where(User.email == email)
    )).scalar()
    if not user or not verify_password(req.password, user.password_hash):
        db.add(LoginAttempt(phone=email, success=False))
        await db.flush()
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    if user.is_disabled:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    db.add(LoginAttempt(phone=email, success=True))
    token = create_access_token({"user_id": user.id, "role": user.role})
    return success({
        "token": token,
        "user": _user_dict(user),
    })


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """忘记密码 — 验证邮箱验证码后重置密码。"""
    email = req.email.strip().lower()

    # 校验邮箱是否已注册
    user = (await db.execute(
        select(User).where(User.email == email)
    )).scalar()
    if not user:
        raise HTTPException(status_code=400, detail="该邮箱未注册")

    # 校验验证码
    sms = (await db.execute(
        select(SmsCode).where(
            SmsCode.phone == email,
            SmsCode.code == req.code,
            SmsCode.purpose == "reset_password",
            SmsCode.used == False,
            SmsCode.expires_at > datetime.now(timezone.utc),
        ).order_by(SmsCode.created_at.desc())
    )).scalar()
    if not sms:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    sms.used = True

    # 更新密码
    user.password_hash = hash_password(req.new_password)
    await db.flush()

    return success(message="密码重置成功")


@router.post("/logout")
async def logout(current_user=Depends(get_current_user)):
    """登出 — 客户端删除 JWT token 即可。"""
    return success(message="已登出")
