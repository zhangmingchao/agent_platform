from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from auth import get_current_user
from services.skill_service import create_skill, delete_skill, get_skill, list_skills

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.get("")
async def api_list_skills(request: Request):
    user = get_current_user(request)
    return await list_skills(user["user_id"])


@router.get("/{skill_id}")
async def api_get_skill(skill_id: int, request: Request):
    user = get_current_user(request)
    skill = await get_skill(skill_id, user["user_id"])
    if not skill:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    return skill


@router.post("/upload")
async def api_upload_skill(request: Request, file: UploadFile = File(...)):
    user = get_current_user(request)
    content = await file.read()
    content_text = content.decode("utf-8")

    name = file.filename.replace(".md", "").replace(".txt", "")
    description = ""
    for line in content_text.split("\n")[:5]:
        line = line.strip()
        if line.startswith("# "):
            name = line[2:].strip() or name
        elif line.startswith("description:"):
            description = line.split(":", 1)[1].strip()

    return await create_skill(user["user_id"], name, description, content_text)


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
