"""独立插件 Worker：领取数据库持久化任务，不把凭据写入消息队列。"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import BaseModel

from .database import close_pool, execute, fetch_one, init_db
from .plugins.packages import ProcessResult
from .plugins.storage import InstalledPackage
from .security import decrypt_plugin_token
from .services import plugin_service as service
from .services.plugin_package_service import PluginExecution, SandboxPluginResult, call_sandbox

log = logging.getLogger(__name__)


class ClaimedTask(BaseModel):
    """已领取任务；kind 区分安装和执行，row 为数据库快照，领取动作在事务内完成。"""

    kind: str
    row: dict[str, Any]


async def claim_task() -> ClaimedTask | None:
    """事务锁定并领取一项任务；多个 Worker 不会同时领取同一数据库记录。"""
    async with service._transaction() as cursor:
        # 优先处理交互调用，避免新安装任务连续到达导致 Agent 一直等待。
        await cursor.execute("SELECT * FROM plugin_executions WHERE status='queued' ORDER BY created_at LIMIT 1 FOR UPDATE")
        row = await cursor.fetchone()
        if row:
            await cursor.execute("UPDATE plugin_executions SET status='running',updated_at=UTC_TIMESTAMP() WHERE id=%s", (row["id"],))
            return ClaimedTask(kind="execute", row=row)
        await cursor.execute("SELECT * FROM plugin_packages WHERE status='queued' ORDER BY created_at LIMIT 1 FOR UPDATE")
        row = await cursor.fetchone()
        if row:
            await cursor.execute("UPDATE plugin_packages SET status='installing',updated_at=UTC_TIMESTAMP() WHERE user_id=%s AND plugin_id=%s AND version=%s", (row["user_id"], row["plugin_id"], row["version"]))
            return ClaimedTask(kind="install", row=row)
    return None


async def run_with_cancellation(user_id: int, plugin_id: str, version: str, execution_id: str, snapshot: PluginExecution) -> SandboxPluginResult:
    """执行固定身份及版本的 snapshot；轮询 execution_id 的取消标记，通知失败时继续重试。"""
    operation = asyncio.create_task(call_sandbox("run", user_id, plugin_id, version, execution_id, snapshot))
    try:
        while not operation.done():
            await asyncio.wait({operation}, timeout=0.5)
            if operation.done():
                break
            row = await fetch_one("SELECT cancel_requested FROM plugin_executions WHERE id=%s AND user_id=%s", (execution_id, user_id))
            if row and row["cancel_requested"]:
                try:
                    await call_sandbox("cancel", user_id, plugin_id, version, execution_id)
                except Exception:
                    log.warning("取消通知暂时失败 execution=%s，将重新尝试", execution_id)
        return await operation
    except Exception:
        # HTTP 超时不代表 Manager 中的排队/执行已停止，仍需送达取消标记。
        try:
            await call_sandbox("cancel", user_id, plugin_id, version, execution_id)
        except Exception:
            log.warning("执行服务异常后的取消通知失败 execution=%s", execution_id)
        raise
    finally:
        if not operation.done():
            # Worker 停止或监测失败时也取消容器任务，防止失去接收方后继续执行业务。
            try:
                await asyncio.shield(call_sandbox("cancel", user_id, plugin_id, version, execution_id))
            except Exception:
                log.warning("Worker 退出时取消通知失败 execution=%s", execution_id)
            operation.cancel()
            await asyncio.gather(operation, return_exceptions=True)


async def process_task(task: ClaimedTask) -> None:
    """执行 task 并保存终态；失败不会自动重试有副作用的业务工具。"""
    row = task.row
    user_id, plugin_id, version = row["user_id"], row["plugin_id"], row["version"]
    if task.kind == "install":
        package = InstalledPackage.model_validate(row)
        try:
            result = await call_sandbox("install", user_id, plugin_id, version, "install")
            if result.status != "completed":
                raise RuntimeError("插件依赖安装失败，请检查固定版本依赖和容器网络")
            async with service._transaction() as cursor:
                await cursor.execute("SELECT id FROM users WHERE id=%s FOR UPDATE", (user_id,))
                await cursor.fetchone()
                await cursor.execute("SELECT version FROM plugin_packages WHERE user_id=%s AND plugin_id=%s AND active=1", (user_id, plugin_id))
                first = not await cursor.fetchone()
                await cursor.execute("UPDATE plugin_packages SET status='ready',active=%s,error_message='',updated_at=UTC_TIMESTAMP() WHERE user_id=%s AND plugin_id=%s AND version=%s", (first, user_id, plugin_id, version))
                await service._audit(cursor, user_id, plugin_id, "install", message=f"版本 {package.version} 已准备完成")
        except Exception:
            log.exception("插件安装失败 user=%s plugin=%s", user_id, plugin_id)
            await execute("UPDATE plugin_packages SET status='failed',error_message=%s,updated_at=UTC_TIMESTAMP() WHERE user_id=%s AND plugin_id=%s AND version=%s", ("依赖准备失败，请检查包依赖、容器网络及 Worker 日志", user_id, plugin_id, version))
        return
    snapshot = None
    status = "failed"
    outcome = ProcessResult(ok=False, error={"code": "EXECUTION_FAILED", "message": "插件执行失败"})
    try:
        snapshot = PluginExecution.model_validate_json(decrypt_plugin_token(row["encrypted_request"]))
        if row["cancel_requested"]:
            status = "cancelled"
            outcome = ProcessResult(ok=False, error={"code": "CANCELLED", "message": "任务已取消"})
        else:
            if snapshot.manifest.id != plugin_id or snapshot.manifest.version != version:
                raise ValueError("执行快照身份不一致")
            result = await run_with_cancellation(user_id, plugin_id, version, row["id"], snapshot)
            if result.status != "completed":
                status = result.status
                outcome = ProcessResult(ok=False, error={"code": result.status.upper(), "message": result.error or "插件进程失败"})
            else:
                outcome = ProcessResult.model_validate_json(result.stdout)
                definition = next(tool for tool in snapshot.manifest.tool_definitions if tool.name == snapshot.tool_name)
                if outcome.ok:
                    Draft202012Validator(definition.output_schema).validate(outcome.data)
                    from .plugins.files import register_artifacts
                    from .runtime.models import RuntimeContext
                    artifacts = await register_artifacts(RuntimeContext(user_id=user_id, session_id=snapshot.session_id), row["id"])
                    outcome.artifacts = artifacts
                else:
                    outcome.artifacts = []
                status = "completed" if outcome.ok else "failed"
    except Exception as exc:
        # 异常不输出请求/凭据；JSON 校验错误可能包含业务输入，所以只记录异常类型。
        log.warning("插件执行失败 execution=%s type=%s", row["id"], type(exc).__name__)
        outcome = ProcessResult(ok=False, error={"code": "INVALID_RESULT", "message": "插件结果无效或执行服务不可用"})
    from .models.plugin import PluginSettings
    output = service.redacted_result(outcome.model_dump_json(), snapshot.manifest, PluginSettings(values=snapshot.values, secrets=snapshot.secrets)) if snapshot else outcome.model_dump_json()
    await execute("UPDATE plugin_executions SET status=%s,result_json=%s,encrypted_request='',updated_at=UTC_TIMESTAMP() WHERE id=%s", (status, output, row["id"]))


async def run_worker() -> None:
    """持续领取插件任务；每进程一次处理一个任务，可启动多个进程提高用户间并发。"""
    await init_db()
    log.info("插件 Worker 已启动")
    while True:
        try:
            # 任务有容器硬超时；过期的运行记录标记失败，不重复执行业务。
            await execute("UPDATE plugin_executions SET status='failed',encrypted_request='',updated_at=UTC_TIMESTAMP() WHERE status='running' AND updated_at<DATE_SUB(UTC_TIMESTAMP(), INTERVAL 10 MINUTE)")
            await execute("UPDATE plugin_packages SET status='failed',error_message='Worker 中断，请重新上传相同包重试',updated_at=UTC_TIMESTAMP() WHERE status='installing' AND updated_at<DATE_SUB(UTC_TIMESTAMP(), INTERVAL 10 MINUTE)")
            task = await claim_task()
            if task is None:
                await asyncio.sleep(0.5)
            else:
                await process_task(task)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("插件 Worker 调度异常")
            await asyncio.sleep(1)


def main() -> None:
    """启动插件 Worker 事件循环，并在停止时关闭数据库连接池。"""
    async def runner() -> None:
        """确保调度循环退出后连接资源清理完成。"""
        try:
            await run_worker()
        finally:
            await close_pool()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        log.info("插件 Worker 已停止")


if __name__ == "__main__":
    main()
