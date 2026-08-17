#!/bin/bash
# Agent Platform (LangChain) 启动脚本
# 使用方法: ./start.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="${SCRIPT_DIR}/backend/.venv-langchan"

# 如果项目内没有 venv，使用其他可能的路径
if [ ! -f "${VENV_PATH}/bin/python" ]; then
    VENV_PATH="${SCRIPT_DIR}/backend/.venv-langchain"
fi

if [ ! -f "${VENV_PATH}/bin/python" ]; then
    VENV_PATH="${SCRIPT_DIR}/.venv-langchain"
fi

if [ ! -f "${VENV_PATH}/bin/python" ]; then
    echo "虚拟环境不存在，正在创建..."
    VENV_PATH="${SCRIPT_DIR}/backend/.venv-langchain"
    PYTHONHOME="" PYTHONPATH="" /opt/homebrew/bin/python3.11 -m venv "${VENV_PATH}"
    PYTHONHOME="" PYTHONPATH="" "${VENV_PATH}/bin/pip" install --upgrade pip
    PYTHONHOME="" PYTHONPATH="" "${VENV_PATH}/bin/pip" install -r "${SCRIPT_DIR}/backend/requirements.txt"
fi

echo "============================================"
echo "  Agent Platform (LangChain) 启动中..."
echo "  前端: http://127.0.0.1:20000/"
echo "  API 文档: http://127.0.0.1:20000/docs"
echo "  默认账号: admin / 123456"
echo "  数据库: agent_platform_langchain"
echo "============================================"

cd "${SCRIPT_DIR}"
PYTHONHOME="" PYTHONPATH="" "${VENV_PATH}/bin/python" -m backend.main
