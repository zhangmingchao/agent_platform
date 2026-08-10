"""Agent Platform FastAPI application entry point."""

import logging
import os
import sys

# Support both `python -m backend.main` and running main.py directly from an IDE.
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "backend"

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import SERVER_PORT
from .database import init_db
from .routers.agents import router as agents_router
from .routers.auth import router as auth_router
from .routers.chat import router as chat_router
from .routers.mcp_configs import router as mcp_configs_router
from .routers.sessions import router as sessions_router
from .routers.skills import router as skills_router
from .routers.traces import router as traces_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("agent-platform")

app = FastAPI(title="Agent Platform")

app.include_router(auth_router)
app.include_router(agents_router)
app.include_router(skills_router)
app.include_router(mcp_configs_router)
app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(traces_router)


@app.on_event("startup")
async def startup():
    await init_db()
    log.info("数据库初始化完成")


frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(frontend_dist, "assets")),
        name="assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


if __name__ == "__main__":
    import uvicorn

    log.info("Agent Platform 启动中... 端口=%s", SERVER_PORT)
    log.info("前端地址: http://127.0.0.1:%s/", SERVER_PORT)
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
