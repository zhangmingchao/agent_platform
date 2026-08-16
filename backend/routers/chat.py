import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from ..auth import get_current_user
from ..crewai_engine import chat_stream
from ..database import execute, fetch_all, fetch_one
from ..services.crew_service import get_crew
from ..services.flow_service import get_flow
from ..services.trace_service import create_trace, finish_trace

router = APIRouter(prefix="/api/chat", tags=["Chat"])
log = logging.getLogger("agent-platform")


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def _create_chat_response(user: Dict, message: str, session_id: int):
    """对话流式接口的核心处理逻辑：
    1. 根据 session_id 查出对话绑定的执行目标（Crew 或 Flow）
    2. 加载历史消息 + 保存用户本次输入
    3. 创建 Trace 记录本次调用链
    4. 启动 chat_stream 流式生成器，把事件转成 SSE 推给前端
    5. 全部结束后保存助手回复 + 完成 Trace
    """
    # ===== 第 1 步：查会话，确认执行目标存在且属于当前用户 =====
    session = await fetch_one(
        "SELECT id, target_type, target_id FROM chat_sessions WHERE id=%s AND user_id=%s",
        (session_id, user["user_id"]),
    )
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在，请重新创建会话")
    # 根据 target_type 决定加载 Crew 还是 Flow（runtime=True 表示需要带运行时配置）
    if session["target_type"] == "crew":
        target = await get_crew(session["target_id"], user["user_id"], runtime=True)
    else:
        target = await get_flow(session["target_id"], user["user_id"])
    if not target or not target.get("enabled", True):
        raise HTTPException(status_code=404, detail="执行目标不存在或已禁用")

    # ===== 第 2 步：加载历史消息（供 LLM 多轮对话上下文） =====
    history = await fetch_all(
        "SELECT role, content FROM chat_messages WHERE session_id=%s ORDER BY id", (session_id,)
    )
    history_messages = [{"role": item["role"], "content": item["content"]} for item in history]

    # ===== 第 3 步：把用户本次输入落库 =====
    await execute(
        "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (%s, %s, %s, %s)",
        (session_id, "user", message, _now()),
    )
    # 如果是新会话（没有任何历史消息），用首条消息前 50 字作为会话标题
    if not history:
        title = message[:50].replace("\n", " ").strip() or "新对话"
        await execute("UPDATE chat_sessions SET title=%s WHERE id=%s", (title, session_id))

    # ===== 第 4 步：创建 Trace 调用链记录（trace_runs 表） =====
    # 用于后续在 Trace 页查看本次对话的完整调用过程
    # model 字段记录本次对话使用的主模型，用于 Trace 列表展示
    model = ""
    if session["target_type"] == "crew":
        if target.get("agents"):
            model = target["agents"][0].get("model", "")
    elif session["target_type"] == "flow":
        # Flow 情况下，从所有 crew 节点里取第一个有 model 的 Agent 作为主模型
        # Flow 可能串多个 Crew，每个 Crew 模型不同，这里只取一个做展示用
        crew_ids = [
            node.get("crew_id") for node in (target.get("nodes") or [])
            if node.get("node_type") == "crew" and node.get("crew_id")
        ]
        if crew_ids:
            # 按 crew_ids 顺序优先取（保留 flow 节点顺序），找不到再兜底取任意一个
            placeholders_in = ",".join(["%s"] * len(crew_ids))
            placeholders_field = ",".join(["%s"] * len(crew_ids))
            row = await fetch_one(
                "SELECT a.model FROM agents a "
                "JOIN crew_agents ca ON ca.agent_id=a.id "
                f"WHERE ca.crew_id IN ({placeholders_in}) AND a.model IS NOT NULL AND a.model != '' "
                f"ORDER BY FIELD(ca.crew_id, {placeholders_field}), ca.crew_id, ca.agent_id LIMIT 1",
                tuple(crew_ids) + tuple(crew_ids),
            )
            if row:
                model = row.get("model", "")
    trace_id = await create_trace(
        user_id=user["user_id"], target_type=session["target_type"],
        target_id=session["target_id"], target_name=target.get("name", ""),
        session_id=session_id, user_message=message, model=model,
    )
    trace_started = time.time()

    # ===== 第 5 步：定义 SSE 流式生成器 =====
    # 这个生成器会被 StreamingResponse 包装后返回给前端
    # 它一边消费 chat_stream 产出的事件，一边做"副作用"：拼接助手回复文本 + 统计 token
    async def generate():
        current_phase_response = []   # 当前阶段（Task）累积的文本片段
        final_response = None         # 最终完整回复（优先用 result 事件的内容）
        # 本轮对话的 token 消耗（来自 usage 事件），默认 0
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        try:
            # 消费 chat_stream 产出的 SSE 事件
            async for chunk in chat_stream(
                target_type=session["target_type"], target_definition=target,
                user_id=user["user_id"], user_message=message,
                history_messages=history_messages, session_id=session_id, trace_id=trace_id,
            ):
                # 解析 SSE 数据（格式："data:{json}\n\n"）
                if chunk.startswith("data:"):
                    try:
                        event = json.loads(chunk[5:].strip())
                        # 进入新阶段（Task 切换）→ 清空当前阶段累积
                        if event.get("type") == "phase_start":
                            current_phase_response = []
                        # 文本片段 → 累积起来（用于最终落库）
                        elif event.get("type") == "chunk":
                            current_phase_response.append(event.get("content", ""))
                        # Token 消耗统计 → 保存起来（完成 Trace 时落库）
                        elif event.get("type") == "usage":
                            prompt_tokens = int(event.get("prompt_tokens", 0) or 0)
                            completion_tokens = int(event.get("completion_tokens", 0) or 0)
                            total_tokens = int(event.get("total_tokens", 0) or 0)
                        # 最终结果 → 直接使用（优先级高于累积）
                        elif event.get("type") == "result":
                            final_response = event.get("content", "")
                    except json.JSONDecodeError:
                        pass
                # 把 chunk 原样转发给前端
                yield chunk

        # ===== 客户端断开连接（如用户关了页面） =====
        except asyncio.CancelledError:
            partial_response = final_response if final_response is not None else "".join(current_phase_response)
            await finish_trace(
                trace_id, "cancelled", partial_response, "客户端断开连接",
                int((time.time() - trace_started) * 1000),
                prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )
            return

        # ===== 执行过程中抛异常 =====
        except Exception as exc:
            log.exception("[Trace#%s] CrewAI 执行失败", trace_id)
            partial_response = final_response if final_response is not None else "".join(current_phase_response)
            await finish_trace(
                trace_id, "error", partial_response, str(exc),
                int((time.time() - trace_started) * 1000),
                prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )
            # 给前端推一条 error 事件，让前端 UI 显示错误提示
            yield f"data:{json.dumps({'type': 'error', 'content': str(exc)}, ensure_ascii=False)}\n\n"
            return

        # ===== 正常完成：保存助手回复 + 完成 Trace =====
        # 优先用 final_response（来自 result 事件），没有就用累积的文本片段
        assistant_text = final_response if final_response is not None else "".join(current_phase_response)
        if assistant_text.strip():
            await execute(
                "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (%s, %s, %s, %s)",
                (session_id, "assistant", assistant_text, _now()),
            )
        await finish_trace(
            trace_id, "success", assistant_text,
            duration_ms=int((time.time() - trace_started) * 1000),
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    # 返回 StreamingResponse，设置 SSE 必需的响应头
    # X-Accel-Buffering: no —— 关闭 Nginx 缓冲，保证流式实时推送
    return StreamingResponse(generate(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no",
    })


# POST /api/chat/stream —— 前端聊天框"发送"按钮调用的接口（主流式对话接口）
@router.post("/stream")
async def api_chat_stream_post(
    request: Request,
    user: Dict = Depends(get_current_user),
):
    body = await request.json()
    message, session_id = body.get("message", ""), body.get("session_id")
    # 参数校验：消息非空 + session_id 必须是整数
    if not isinstance(message, str) or not message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    if not isinstance(session_id, int):
        raise HTTPException(status_code=400, detail="需要有效的 session_id")
    return await _create_chat_response(user, message, session_id)


# GET /api/chat/stream —— 备用的 GET 版本（某些场景下 SSE 只能用 GET，如 EventSource）
@router.get("/stream")
async def api_chat_stream_get(
    message: str = Query(...),
    session_id: int = Query(...),
    token: Optional[str] = Query(None),
    user: Dict = Depends(get_current_user),
):
    return await _create_chat_response(user, message, session_id)
