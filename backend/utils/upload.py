"""
文件上传工具 — 验证/保存/路径生成。
"""
import os
import uuid
import hashlib
from datetime import datetime

from fastapi import HTTPException, UploadFile

from config import get_settings

settings = get_settings()

# 允许的文件类型
ALLOWED_EXTENSIONS = {
    "image": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"},
    "video": {".mp4", ".mov", ".avi", ".webm"},
    "document": {".pdf", ".txt", ".md"},
}

# 最大文件大小（字节）
MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def allowed_file(filename: str, category: str = "image") -> bool:
    """检查文件扩展名是否在允许范围内。"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS.get(category, set())


def generate_filename(original: str) -> str:
    """生成唯一文件名：日期/uuidhash.ext"""
    ext = os.path.splitext(original)[1].lower()
    uid = uuid.uuid4().hex[:12]
    today = datetime.now().strftime("%Y%m")
    hash_part = hashlib.md5(f"{uid}{original}".encode()).hexdigest()[:8]
    return f"{today}/{uid}_{hash_part}{ext}"


async def save_upload(file: UploadFile, subdir: str = "images") -> str:
    """保存上传文件并返回相对路径。

    Args:
        file: FastAPI UploadFile 对象
        subdir: 子目录（images/videos/documents）

    Returns:
        相对路径，如 "images/202601/abc123_ef456789.jpg"

    Raises:
        HTTPException: 文件类型不允许或大小超限
    """
    # 检查文件类型
    if not allowed_file(file.filename or "", category="image" if subdir == "images" else "document"):
        raise HTTPException(400, detail="不支持的文件格式")

    # 检查文件大小
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(400, detail=f"文件大小不能超过{settings.MAX_UPLOAD_SIZE_MB}MB")

    await file.seek(0)

    # 生成存储路径
    filename = generate_filename(file.filename or "file")
    rel_path = os.path.join(subdir, filename)
    abs_path = os.path.join(settings.UPLOAD_DIR, rel_path)

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    with open(abs_path, "wb") as f:
        f.write(content)

    return rel_path.replace("\\", "/")
