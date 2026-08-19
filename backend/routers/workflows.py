import asyncio
import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..auth import get_current_user
from ..services.workflow_service import (
    create_workflow,
    delete_workflow,
    execute_workflow_run,
    get_workflow,
    get_workflow_run,
    list_workflow_runs,
    list_workflows,
    start_workflow_run,
    update_workflow,
)

router = APIRouter(prefix="/api/workflows", tags=["Multi-Agent Workflows"])
log = logging.getLogger("agent-platform")


def _sse_event(event_type: str, payload: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _execute_run_safely(run_id: int, user_id: int):
    try:
        await execute_workflow_run(run_id, user_id)
    except Exception:
        log.exception("[WorkflowRun#%s] background execution failed", run_id)


@router.get("")
async def api_list_workflows(user: dict = Depends(get_current_user)):
    return await list_workflows(user["user_id"])


@router.post("")
async def api_create_workflow(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    return await create_workflow(user["user_id"], body)


@router.get("/{workflow_id}")
async def api_get_workflow(workflow_id: int, user: dict = Depends(get_current_user)):
    workflow = await get_workflow(workflow_id, user["user_id"])
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return workflow


@router.put("/{workflow_id}")
async def api_update_workflow(workflow_id: int, request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    workflow = await update_workflow(workflow_id, user["user_id"], body)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return workflow


@router.delete("/{workflow_id}")
async def api_delete_workflow(workflow_id: int, user: dict = Depends(get_current_user)):
    success = await delete_workflow(workflow_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return {"success": True}


@router.post("/{workflow_id}/run")
async def api_run_workflow(
    workflow_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    body = await request.json()
    input_text = body.get("input", "")
    if not isinstance(input_text, str) or not input_text.strip():
        raise HTTPException(status_code=400, detail="input 不能为空")
    run = await start_workflow_run(workflow_id, user["user_id"], input_text)
    background_tasks.add_task(_execute_run_safely, run["run_id"], user["user_id"])
    return run


@router.get("/{workflow_id}/runs")
async def api_list_workflow_runs(workflow_id: int, user: dict = Depends(get_current_user)):
    return await list_workflow_runs(workflow_id, user["user_id"])


@router.get("/runs/{run_id}")
async def api_get_workflow_run(run_id: int, user: dict = Depends(get_current_user)):
    run = await get_workflow_run(run_id, user["user_id"])
    if not run:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    return run


@router.get("/runs/{run_id}/events")
async def api_stream_workflow_run_events(run_id: int, user: dict = Depends(get_current_user)):
    if not await get_workflow_run(run_id, user["user_id"]):
        raise HTTPException(status_code=404, detail="运行记录不存在")

    async def generate():
        last_signature = None
        while True:
            run = await get_workflow_run(run_id, user["user_id"])
            if not run:
                yield _sse_event("error", {"detail": "运行记录不存在"})
                return

            signature = json.dumps(run, ensure_ascii=False, default=str)
            if signature != last_signature:
                last_signature = signature
                yield _sse_event("snapshot", run)

            if run["status"] in ("success", "error", "cancelled"):
                yield _sse_event("done", run)
                return

            yield _sse_event("ping", {"run_id": run_id})
            await asyncio.sleep(1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
