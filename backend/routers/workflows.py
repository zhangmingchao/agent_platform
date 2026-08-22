"""多 Agent 工作流 HTTP 路由与 SSE 事件订阅接口。"""

import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..auth import get_current_user
from ..core.event_publisher import workflow_event_stream_key
from ..redis_client import get_redis
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


def _sse_event(event_id: str, event_type: str, payload: dict) -> str:
    """按照 SSE 协议编码事件，Redis Stream ID 直接作为 SSE 的 id。"""
    return (
        f"id: {event_id}\n"
        f"event: {event_type}\n"
        f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    )


async def _execute_run_safely(run_id: int, user_id: int):
    """在后台执行工作流并记录未被业务层处理的异常。"""
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
    """创建 run 后立即返回，实际工作流在响应结束后的后台任务中执行。"""
    body = await request.json()
    input_text = body.get("input", "")
    if not isinstance(input_text, str) or not input_text.strip():
        raise HTTPException(status_code=400, detail="input 不能为空")
    run = await start_workflow_run(workflow_id, user["user_id"], input_text)
    # 创建与订阅拆分后，即使 SSE 连接断开，此后台任务也不会被浏览器取消。
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
    """从 Redis Stream 读取指定 run 的事件并转换成 SSE 数据流。

    当前版本暂不处理 Last-Event-ID，因此每次订阅都从 0-0 开始读取完整事件。
    """
    if not await get_workflow_run(run_id, user["user_id"]):
        raise HTTPException(status_code=404, detail="运行记录不存在")

    async def generate():
        # 0-0 表示从 Stream 第一条事件开始；后续可替换为 Last-Event-ID。
        cursor = "0-0"
        redis = await get_redis()
        stream_key = workflow_event_stream_key(run_id)
        while True:
            results = await redis.xread(
                streams={stream_key: cursor},
                count=100,
                block=15000,
            )
            if not results:
                # SSE 注释行不会触发前端业务事件，只用于维持代理和浏览器连接。
                yield ": heartbeat\n\n"
                continue

            for _, events in results:
                for event_id, fields in events:
                    # 游标更新为本批次最后处理的 ID，下一次 XREAD 只返回其后的事件。
                    cursor = event_id
                    event_type = fields["type"]
                    payload = json.loads(fields.get("payload") or "{}")
                    event_data = {
                        **payload,
                        "id": event_id,
                        "type": event_type,
                        "runId": int(fields["runId"]),
                        "nodeId": fields.get("nodeId") or None,
                        "sequence": int(fields["sequence"]),
                    }
                    yield _sse_event(event_id, event_type, event_data)

                    # 收到终态事件后主动关闭 SSE，避免无意义地继续占用连接。
                    if event_type in ("done", "error", "cancelled"):
                        return

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
