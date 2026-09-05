import os
from urllib.parse import quote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SKILLS_DIR = os.path.join(DATA_DIR, "skills")
RUNTIME_DATA_DIR = os.path.join(DATA_DIR, "runtime")


os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SKILLS_DIR, exist_ok=True)
os.makedirs(RUNTIME_DATA_DIR, exist_ok=True)

JWT_SECRET = os.getenv("JWT_SECRET", "agent-platform-secret-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# --- 大语言模型（DeepSeek，兼容 OpenAI 接口）---
DEEPSEEK_API_KEY = ""
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

LLM_MODEL_OPTIONS = [
    {"value": "deepseek-chat", "label": "deepseek-chat"},
    {"value": "deepseek-reasoner", "label": "deepseek-reasoner"},
    {"value": "deepseek-v4-flash", "label": "deepseek-v4-flash"},
    {"value": "deepseek-v4-pro", "label": "deepseek-v4-pro"},
]

# --- 数据库 ---
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_NAME = os.getenv("DB_NAME", "agent_platform_langchain")

# --- Redis ---
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
# 工作流 Checkpoint 使用独立 URL，便于生产环境将运行状态放到专用 Redis。
_redis_auth = f":{quote(REDIS_PASSWORD, safe='')}@" if REDIS_PASSWORD else ""
WORKFLOW_CHECKPOINT_REDIS_URL = os.getenv(
    "WORKFLOW_CHECKPOINT_REDIS_URL",
    f"redis://{_redis_auth}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
)
# 官方 Redis Checkpointer 的 TTL 单位为分钟，默认保留七天运行现场。
WORKFLOW_CHECKPOINT_TTL_MINUTES = float(
    os.getenv("WORKFLOW_CHECKPOINT_TTL_MINUTES", "10080")
)
WORKFLOW_EVENT_STREAM_TTL_SECONDS = int(
    os.getenv("WORKFLOW_EVENT_STREAM_TTL_SECONDS", "86400")
)
WORKFLOW_EVENT_STREAM_MAXLEN = int(
    os.getenv("WORKFLOW_EVENT_STREAM_MAXLEN", "20000")
)

# --- MongoDB Trace Span 存储（强依赖，不可用时服务拒绝启动）---
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://agent_platform_root:agent-platform-mongo-local-2026@127.0.0.1:27017/?authSource=admin",
)
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "agent_platform_trace")
MONGODB_TRACE_SPANS_COLLECTION = os.getenv("MONGODB_TRACE_SPANS_COLLECTION", "trace_spans")
MONGODB_CONNECT_TIMEOUT_MS = int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000"))
MONGODB_TRACE_RETENTION_DAYS = int(os.getenv("MONGODB_TRACE_RETENTION_DAYS", "90"))

# --- 服务器 ---
SERVER_PORT = int(os.getenv("SERVER_PORT", "20000"))
MAX_TOOL_ROUNDS = 6

# --- 本地 Python Runtime ---
PYTHON_RUNTIME_ENABLED = os.getenv("PYTHON_RUNTIME_ENABLED", "true").lower() in (
    "1", "true", "yes", "on",
)
PYTHON_RUNTIME_TIMEOUT_SECONDS = int(os.getenv("PYTHON_RUNTIME_TIMEOUT_SECONDS", "30"))
PYTHON_RUNTIME_MAX_TIMEOUT_SECONDS = int(os.getenv("PYTHON_RUNTIME_MAX_TIMEOUT_SECONDS", "30"))
PYTHON_RUNTIME_MEMORY_MB = int(os.getenv("PYTHON_RUNTIME_MEMORY_MB", "512"))
PYTHON_RUNTIME_MAX_UPLOAD_MB = int(os.getenv("PYTHON_RUNTIME_MAX_UPLOAD_MB", "20"))
PYTHON_RUNTIME_MAX_OUTPUT_MB = int(os.getenv("PYTHON_RUNTIME_MAX_OUTPUT_MB", "20"))
RUNTIME_WORKER_QUEUE_NAME = os.getenv("RUNTIME_WORKER_QUEUE_NAME", "runtime:execution:queue")
RUNTIME_WORKER_QUEUE_WAIT_SECONDS = int(os.getenv("RUNTIME_WORKER_QUEUE_WAIT_SECONDS", "30"))
RUNTIME_WORKER_RESULT_TTL_SECONDS = int(os.getenv("RUNTIME_WORKER_RESULT_TTL_SECONDS", "3600"))
SANDBOX_SERVICE_URL = os.getenv("SANDBOX_SERVICE_URL", "http://127.0.0.1:20002").rstrip("/")
SANDBOX_SERVICE_TOKEN = os.getenv("SANDBOX_SERVICE_TOKEN", "change-me-in-production")
SANDBOX_REQUEST_TIMEOUT_SECONDS = int(os.getenv("SANDBOX_REQUEST_TIMEOUT_SECONDS", "45"))

# --- 技能 HTTP 动作 ---
SKILL_ACTION_ALLOW_PRIVATE_NETWORK = os.getenv(
    "SKILL_ACTION_ALLOW_PRIVATE_NETWORK",
    "false",
).lower() in ("1", "true", "yes", "on")

# --- LangSmith（链路追踪）---
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "agent-platform-langchain")

if LANGSMITH_API_KEY:
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_API_KEY", LANGSMITH_API_KEY)
    os.environ.setdefault("LANGCHAIN_PROJECT", LANGSMITH_PROJECT)
    os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
