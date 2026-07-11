"""
文件上传 — 公共端点，复用 utils/upload.py 的 save_upload()。
"""
from fastapi import APIRouter, UploadFile, File, HTTPException

from utils.upload import save_upload
from utils.response import success

router = APIRouter(tags=["文件上传"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传图片文件，返回可访问的 URL 路径。

    前端使用 multipart/form-data，字段名 `file`。
    返回格式：{ code: 0, data: { url: "/uploads/images/202607/xxx.jpg" } }
    """
    if not file.filename:
        raise HTTPException(400, detail="请选择文件")

    rel_path = await save_upload(file, subdir="images")
    return success({"url": f"/uploads/{rel_path}"})
