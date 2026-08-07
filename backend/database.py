"""
Database layer - MySQL with aiomysql for async operations.
Tables: users, agents, agent_skills, agent_mcps, skills, mcp_configs,
        chat_sessions, chat_messages
"""
import aiomysql
import logging
from datetime import datetime
from typing import Optional, List, Dict

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

log = logging.getLogger("agent-platform")

_pool: Optional[aiomysql.Pool] = None


async def get_pool() -> aiomysql.Pool:
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
            charset="utf8mb4",
            autocommit=False,
        )
    return _pool


async def get_conn() -> aiomysql.Connection:
    pool = await get_pool()
    return await pool.acquire()


async def release_conn(conn: aiomysql.Connection):
    pool = await get_pool()
    pool.release(conn)


async def init_db():
    conn = await get_conn()
    try:
        async with conn.cursor() as cur:
            await cur.execute("CREATE DATABASE IF NOT EXISTS `%s` DEFAULT CHARACTER SET utf8mb4" % DB_NAME)
            await cur.execute("USE `%s`" % DB_NAME)
            await conn.commit()

            statements = [
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    created_at DATETIME NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS agents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    system_prompt TEXT,
                    model VARCHAR(100) DEFAULT 'deepseek-chat',
                    temperature FLOAT DEFAULT 0.7,
                    iteration_count INT NOT NULL DEFAULT 6,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_user (user_id),
                    CONSTRAINT fk_agent_user FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS skills (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    content TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    INDEX idx_user (user_id),
                    CONSTRAINT fk_skill_user FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS mcp_configs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    base_url VARCHAR(500) NOT NULL,
                    endpoint VARCHAR(100) DEFAULT '/mcp',
                    description TEXT,
                    created_at DATETIME NOT NULL,
                    INDEX idx_user (user_id),
                    CONSTRAINT fk_mcp_user FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS agent_skills (
                    agent_id INT NOT NULL,
                    skill_id INT NOT NULL,
                    PRIMARY KEY (agent_id, skill_id),
                    INDEX idx_skill (skill_id),
                    CONSTRAINT fk_as_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                    CONSTRAINT fk_as_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS agent_mcps (
                    agent_id INT NOT NULL,
                    mcp_id INT NOT NULL,
                    PRIMARY KEY (agent_id, mcp_id),
                    INDEX idx_mcp (mcp_id),
                    CONSTRAINT fk_am_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                    CONSTRAINT fk_am_mcp FOREIGN KEY (mcp_id) REFERENCES mcp_configs(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    agent_id INT NOT NULL,
                    title VARCHAR(200) DEFAULT '新对话',
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user (user_id),
                    INDEX idx_agent (agent_id),
                    CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES users(id),
                    CONSTRAINT fk_session_agent FOREIGN KEY (agent_id) REFERENCES agents(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    INDEX idx_session (session_id),
                    CONSTRAINT fk_msg_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
            ]

            for sql in statements:
                await cur.execute(sql)

            # Incremental migration for databases created before iteration_count
            await cur.execute("SHOW COLUMNS FROM agents LIKE 'iteration_count'")
            if not await cur.fetchone():
                await cur.execute(
                    "ALTER TABLE agents ADD COLUMN iteration_count INT NOT NULL DEFAULT 6 AFTER temperature"
                )
                log.info("[DB] agents.iteration_count 字段迁移完成")

            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            await cur.execute(
                "INSERT INTO users (username, password, created_at) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE username=username",
                ("admin", "123456", now)
            )
            await cur.execute(
                "INSERT INTO users (username, password, created_at) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE username=username",
                ("test", "123456", now)
            )
            await conn.commit()
            log.info("[DB] 数据库初始化完成，默认用户: admin/123456, test/123456")
    finally:
        await release_conn(conn)


async def fetch_all(sql: str, params: tuple = ()) -> List[Dict]:
    conn = await get_conn()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()
            return list(rows)
    finally:
        await release_conn(conn)


async def fetch_one(sql: str, params: tuple = ()) -> Optional[Dict]:
    conn = await get_conn()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, params)
            row = await cur.fetchone()
            return dict(row) if row else None
    finally:
        await conn.rollback()
        await release_conn(conn)


async def execute(sql: str, params: tuple = ()) -> int:
    conn = await get_conn()
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            await conn.commit()
            return cur.lastrowid
    finally:
        await release_conn(conn)


async def execute_many(sql: str, params_list: List[tuple]):
    conn = await get_conn()
    try:
        async with conn.cursor() as cur:
            await cur.executemany(sql, params_list)
            await conn.commit()
    finally:
        await release_conn(conn)


async def fetch_val(sql: str, params: tuple = ()):
    conn = await get_conn()
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            row = await cur.fetchone()
            return row[0] if row else None
    finally:
        await conn.rollback()
        await release_conn(conn)
