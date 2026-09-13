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

# --- 凭据安全 ---
# 32 字节随机密钥的 URL-safe Base64；仅在保存或读取模型 API Key 时强制要求。
MODEL_API_KEY_ENCRYPTION_KEY = os.getenv("MODEL_API_KEY_ENCRYPTION_KEY", "")
# 只有部署在可信反向代理后方时才允许读取 X-Forwarded-For。
TRUST_PROXY_HEADERS = os.getenv("TRUST_PROXY_HEADERS", "false").lower() in (
    "1", "true", "yes", "on",
)


def _positive_int_env(name: str, default: int) -> int:
    """读取必须大于零的整数环境变量。

    Args:
        name: 环境变量名称。
        default: 环境变量未设置时使用的默认值。

    Returns:
        经过正整数校验的配置值。
    """
    value = int(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} 必须大于 0")
    return value


# 高风险接口的默认限流策略，均可通过环境变量覆盖。
LOGIN_RATE_LIMIT_PER_IP = _positive_int_env("LOGIN_RATE_LIMIT_PER_IP", 10)
LOGIN_RATE_LIMIT_PER_USERNAME = _positive_int_env("LOGIN_RATE_LIMIT_PER_USERNAME", 5)
REGISTER_RATE_LIMIT_PER_IP = _positive_int_env("REGISTER_RATE_LIMIT_PER_IP", 5)
AUTH_RATE_LIMIT_WINDOW_SECONDS = _positive_int_env("AUTH_RATE_LIMIT_WINDOW_SECONDS", 300)
MODEL_TEST_RATE_LIMIT = _positive_int_env("MODEL_TEST_RATE_LIMIT", 10)
MCP_CALL_RATE_LIMIT = _positive_int_env("MCP_CALL_RATE_LIMIT", 30)
CHAT_RATE_LIMIT = _positive_int_env("CHAT_RATE_LIMIT", 30)
WORKFLOW_RUN_RATE_LIMIT = _positive_int_env("WORKFLOW_RUN_RATE_LIMIT", 10)
WORKFLOW_APPROVAL_RATE_LIMIT = _positive_int_env("WORKFLOW_APPROVAL_RATE_LIMIT", 30)
RUNTIME_UPLOAD_RATE_LIMIT = _positive_int_env("RUNTIME_UPLOAD_RATE_LIMIT", 20)
RUNTIME_EXECUTION_RATE_LIMIT = _positive_int_env("RUNTIME_EXECUTION_RATE_LIMIT", 10)
HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS = _positive_int_env(
    "HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS", 60,
)

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
