import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SKILLS_DIR = os.path.join(DATA_DIR, "skills")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SKILLS_DIR, exist_ok=True)

JWT_SECRET = os.getenv("JWT_SECRET", "agent-platform-secret-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_NAME = os.getenv("DB_NAME", "agent_platform")

SERVER_PORT = int(os.getenv("SERVER_PORT", "20000"))
MAX_TOOL_ROUNDS = 5