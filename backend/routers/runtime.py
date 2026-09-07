"""Python Runtime 文件上传、下载与执行查询接口。"""

from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..auth import get_current_user
from ..database import fetch_one
from ..services.runtime_service import get_runtime_file, save_runtime_file

router = APIRouter(prefix="/api/runtime", tags=["Runtime"])


async def _validate_session(session_id: int | None, user_id: int) -> None:
    """校验可选会话是否属于当前用户。"""
    if session_id is None:
        return
    session = await fetch_one(
        "SELECT id FROM chat_sessions WHERE id=%s AND user_id=%s",
        (session_id, user_id),
    )
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")


@router.post("/files")
async def upload_runtime_file(
    file: UploadFile = File(...),
    session_id: int | None = Form(default=None),
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """上传一个 Runtime 输入文件，并返回供模型使用的逻辑文件 ID。"""
    await _validate_session(session_id, user["user_id"])
    try:
        content = await file.read()
        return await save_runtime_file(
            user["user_id"], session_id, file.filename or "file", file.content_type, content,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await file.close()


@router.get("/files/{file_id}")
async def download_runtime_file(file_id: str, user: dict = Depends(get_current_user)) -> FileResponse:
    """下载当前用户上传的文件或 Runtime 产出的 Artifact。"""
    file_info = await get_runtime_file(file_id, user["user_id"])
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")
    path = Path(file_info["storage_path"])
    if not path.is_file():
        raise HTTPException(status_code=410, detail="文件已不在存储中")
    return FileResponse(
        path=str(path),
        media_type=file_info.get("mime_type") or "application/octet-stream",
        filename=file_info["file_name"],
    )

