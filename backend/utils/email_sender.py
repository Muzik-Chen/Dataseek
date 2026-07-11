"""
163 SMTP 邮件发送 — 用于发送验证码。
参考代码风格：EmailMessage + ssl.create_default_context + with 语句。
"""
import ssl
import smtplib
import traceback
from email.message import EmailMessage

from config import get_settings

settings = get_settings()


def send_verification_code(to_email: str, code: str) -> bool:
    """发送验证码邮件。成功返回 True，失败返回 False。"""
    subject = "潮汕文化宣传平台 - 验证码"
    body = f"""您的验证码是：{code}

验证码 5 分钟内有效，请勿泄露给他人。

—— 潮汕文化宣传平台
"""
    return _send_email(to_email, subject, body)


def _send_email(to_email: str, subject: str, body: str) -> bool:
    """底层发送方法。"""
    # 诊断：打印当前 SMTP 配置（密码脱敏）
    print(f"[EMAIL] SMTP 配置: server={settings.SMTP_SERVER}, port={settings.SMTP_PORT}, "
          f"username={settings.SMTP_USERNAME}, "
          f"password={'***' if settings.SMTP_PASSWORD else 'EMPTY!'}, "
          f"from={settings.SMTP_FROM}")

    context = ssl.create_default_context()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT, context=context) as smtp:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
        print(f"[EMAIL] 发送成功 → {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] 发送失败 → {to_email}: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False
