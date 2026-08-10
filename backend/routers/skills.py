from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from ..auth import get_current_user
from ..services.skill_service import (
    create_skill,
    delete_skill,
    extract_skill_archive,
    get_skill,
    list_skill_files,
    list_skills,
    read_skill_file,
    read_skill_archive,
    update_skill_metadata,
    update_skill_file,
)

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.get("")
async def api_list_skills(request: Request):
    user = get_current_user(request)
    return await list_skills(user["user_id"])


@router.get("/{skill_id}/files")
async def api_list_skill_files(skill_id: int, request: Request):
    user = get_current_user(request)
    if not await get_skill(skill_id, user["user_id"]):
        raise HTTPException(status_code=404, detail="Skill 不存在")
    return list_skill_files(skill_id)


@router.get("/{skill_id}/files/{file_path:path}")
async def api_read_skill_file(skill_id: int, file_path: str, request: Request):
    user = get_current_user(request)
    if not await get_skill(skill_id, user["user_id"]):
        raise HTTPException(status_code=404, detail="Skill 不存在")
    try:
        return {"path": file_path, "content": read_skill_file(skill_id, file_path)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{skill_id}/files/{file_path:path}")
async def api_update_skill_file(skill_id: int, file_path: str, request: Request):
    user = get_current_user(request)
    if not await get_skill(skill_id, user["user_id"]):
        raise HTTPException(status_code=404, detail="Skill 不存在")
    body = await request.json()
    content = body.get("content")
    if not isinstance(content, str):
        raise HTTPException(status_code=400, detail="content 必须是字符串")
    try:
        await update_skill_file(skill_id, user["user_id"], file_path, content)
        return {"success": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{skill_id}")
async def api_get_skill(skill_id: int, request: Request):
    user = get_current_user(request)
    skill = await get_skill(skill_id, user["user_id"])
    if not skill:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    return skill


@router.put("/{skill_id}")
async def api_update_skill(skill_id: int, request: Request):
    user = get_current_user(request)
    body = await request.json()
    name = body.get("name", "")
    description = body.get("description", "")
    if not isinstance(name, str) or not name.strip():
        raise HTTPException(status_code=400, detail="技能名称不能为空")
    if not isinstance(description, str):
        raise HTTPException(status_code=400, detail="技能描述必须是字符串")
    skill = await update_skill_metadata(
        skill_id,
        user["user_id"],
        name.strip(),
        description.strip(),
    )
    if not skill:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    return skill


@router.post("/upload")
async def api_upload_skill(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(...),
):
    user = get_current_user(request)
    content = await file.read()
    filename = file.filename or ""
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    try:
        if suffix == "zip":
            # SKILL.md 只提供实际执行内容；名称和描述由创建弹窗明确提交。
            _, _, content_text = read_skill_archive(content)
            clean_name = name.strip()
            clean_description = description.strip()
            if not clean_name:
                raise ValueError("技能名称不能为空")
            if not clean_description:
                raise ValueError("技能描述不能为空")
            skill = await create_skill(user["user_id"], clean_name, clean_description, content_text)
            try:
                # 解压目录以数据库中的 Skill ID 命名，例如 data/skills/42/.
                extract_skill_archive(skill["id"], content)
            except Exception:
                # 文件解压失败时，回滚刚创建的 Skill 记录。
                await delete_skill(skill["id"], user["user_id"])
                raise
            return skill

        raise ValueError("仅支持 .zip 技能包")
    except (UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("")
async def api_create_skill(request: Request):
    user = get_current_user(request)
    body = await request.json()
    return await create_skill(
        user["user_id"],
        body.get("name", ""),
        body.get("description", ""),
        body.get("content", ""),
    )


@router.delete("/{skill_id}")
async def api_delete_skill(skill_id: int, request: Request):
    user = get_current_user(request)
    success = await delete_skill(skill_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    return {"success": True}
