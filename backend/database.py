"""Async MySQL access and non-destructive runtime schema initialization."""
import aiomysql
import logging
import re
from datetime import datetime
from typing import Optional, List, Dict

from .config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

log = logging.getLogger("agent-platform")

_pool: Optional[aiomysql.Pool] = None


async def get_pool() -> aiomysql.Pool:
    global _pool
    if _pool is None:
        bootstrap = await aiomysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset="utf8mb4",
            autocommit=True,
        )
        try:
            async with bootstrap.cursor() as cur:
                await cur.execute(
                    "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME=%s",
                    (DB_NAME,),
                )
                if not await cur.fetchone():
                    safe_db_name = DB_NAME.replace("`", "``")
                    await cur.execute(
                        "CREATE DATABASE `%s` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                        % safe_db_name
                    )
        finally:
            bootstrap.close()
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


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


async def init_db():
    conn = await get_conn()
    try:
        async with conn.cursor() as cur:
            await cur.execute("USE `%s`" % DB_NAME)
            await cur.execute("SET sql_notes = 0")
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
                    role VARCHAR(200) NOT NULL DEFAULT 'AI Agent',
                    goal TEXT,
                    backstory TEXT,
                    system_prompt TEXT,
                    model VARCHAR(100) DEFAULT 'deepseek-chat',
                    temperature FLOAT DEFAULT 0.7,
                    iteration_count INT NOT NULL DEFAULT 6,
                    allow_delegation TINYINT(1) NOT NULL DEFAULT 0,
                    reasoning TINYINT(1) NOT NULL DEFAULT 0,
                    planning TINYINT(1) NOT NULL DEFAULT 0,
                    memory TINYINT(1) NOT NULL DEFAULT 0,
                    enabled TINYINT(1) NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_agent_user (user_id),
                    CONSTRAINT fk_agent_user FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS skills (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    content LONGTEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    INDEX idx_skill_user (user_id),
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
                    INDEX idx_mcp_user (user_id),
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
                CREATE TABLE IF NOT EXISTS crews (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    process VARCHAR(30) NOT NULL DEFAULT 'sequential',
                    manager_agent_id INT NULL,
                    planning TINYINT(1) NOT NULL DEFAULT 0,
                    memory TINYINT(1) NOT NULL DEFAULT 0,
                    cache_enabled TINYINT(1) NOT NULL DEFAULT 0,
                    verbose TINYINT(1) NOT NULL DEFAULT 0,
                    max_rpm INT NULL,
                    enabled TINYINT(1) NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_crew_user (user_id),
                    CONSTRAINT fk_crew_user FOREIGN KEY (user_id) REFERENCES users(id),
                    CONSTRAINT fk_crew_manager FOREIGN KEY (manager_agent_id) REFERENCES agents(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS crew_agents (
                    crew_id INT NOT NULL,
                    agent_id INT NOT NULL,
                    PRIMARY KEY (crew_id, agent_id),
                    INDEX idx_ca_agent (agent_id),
                    CONSTRAINT fk_ca_crew FOREIGN KEY (crew_id) REFERENCES crews(id) ON DELETE CASCADE,
                    CONSTRAINT fk_ca_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS crew_tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    crew_id INT NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description LONGTEXT NOT NULL,
                    expected_output LONGTEXT NOT NULL,
                    agent_id INT NULL,
                    order_no INT NOT NULL DEFAULT 1,
                    async_execution TINYINT(1) NOT NULL DEFAULT 0,
                    human_input TINYINT(1) NOT NULL DEFAULT 0,
                    markdown TINYINT(1) NOT NULL DEFAULT 1,
                    guardrail TEXT,
                    max_retries INT NOT NULL DEFAULT 2,
                    output_file VARCHAR(500),
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_task_crew (crew_id, order_no),
                    INDEX idx_task_agent (agent_id),
                    CONSTRAINT fk_task_crew FOREIGN KEY (crew_id) REFERENCES crews(id) ON DELETE CASCADE,
                    CONSTRAINT fk_task_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    task_id INT NOT NULL,
                    depends_on_task_id INT NOT NULL,
                    PRIMARY KEY (task_id, depends_on_task_id),
                    CONSTRAINT fk_td_task FOREIGN KEY (task_id) REFERENCES crew_tasks(id) ON DELETE CASCADE,
                    CONSTRAINT fk_td_dependency FOREIGN KEY (depends_on_task_id) REFERENCES crew_tasks(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS task_skills (
                    task_id INT NOT NULL,
                    skill_id INT NOT NULL,
                    PRIMARY KEY (task_id, skill_id),
                    CONSTRAINT fk_ts_task FOREIGN KEY (task_id) REFERENCES crew_tasks(id) ON DELETE CASCADE,
                    CONSTRAINT fk_ts_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS task_mcps (
                    task_id INT NOT NULL,
                    mcp_id INT NOT NULL,
                    PRIMARY KEY (task_id, mcp_id),
                    CONSTRAINT fk_tm_task FOREIGN KEY (task_id) REFERENCES crew_tasks(id) ON DELETE CASCADE,
                    CONSTRAINT fk_tm_mcp FOREIGN KEY (mcp_id) REFERENCES mcp_configs(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS flows (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    state_schema_json LONGTEXT,
                    enabled TINYINT(1) NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_flow_user (user_id),
                    CONSTRAINT fk_flow_user FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS flow_nodes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    flow_id INT NOT NULL,
                    node_key VARCHAR(100) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    node_type VARCHAR(30) NOT NULL,
                    crew_id INT NULL,
                    config_json LONGTEXT,
                    position_x INT NOT NULL DEFAULT 0,
                    position_y INT NOT NULL DEFAULT 0,
                    UNIQUE KEY uk_flow_node_key (flow_id, node_key),
                    CONSTRAINT fk_fn_flow FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE,
                    CONSTRAINT fk_fn_crew FOREIGN KEY (crew_id) REFERENCES crews(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS flow_edges (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    flow_id INT NOT NULL,
                    source_node_id INT NOT NULL,
                    target_node_id INT NOT NULL,
                    condition_type VARCHAR(30) NOT NULL DEFAULT 'always',
                    condition_value TEXT,
                    priority INT NOT NULL DEFAULT 0,
                    CONSTRAINT fk_fe_flow FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE,
                    CONSTRAINT fk_fe_source FOREIGN KEY (source_node_id) REFERENCES flow_nodes(id) ON DELETE CASCADE,
                    CONSTRAINT fk_fe_target FOREIGN KEY (target_node_id) REFERENCES flow_nodes(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    target_type VARCHAR(20) NOT NULL,
                    target_id INT NOT NULL,
                    title VARCHAR(200) DEFAULT '新对话',
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_session_user (user_id),
                    INDEX idx_session_target (target_type, target_id),
                    CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES users(id),
                    CHECK (target_type IN ('crew', 'flow'))
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content LONGTEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    INDEX idx_message_session (session_id),
                    CONSTRAINT fk_msg_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS trace_runs (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    target_type VARCHAR(20) NOT NULL,
                    target_id INT NOT NULL,
                    target_name VARCHAR(200),
                    session_id INT NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'running',
                    model VARCHAR(100),
                    input_text LONGTEXT,
                    output_text LONGTEXT,
                    error_text TEXT,
                    started_at DATETIME(6) NOT NULL,
                    ended_at DATETIME(6),
                    duration_ms BIGINT DEFAULT 0,
                    created_at DATETIME(6) NOT NULL,
                    INDEX idx_trace_user (user_id, id),
                    INDEX idx_trace_target (target_type, target_id),
                    INDEX idx_trace_session (session_id),
                    CONSTRAINT fk_trace_user FOREIGN KEY (user_id) REFERENCES users(id),
                    CONSTRAINT fk_trace_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS trace_spans (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    trace_id BIGINT NOT NULL,
                    task_id INT NULL,
                    agent_id INT NULL,
                    span_type VARCHAR(30) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    round_no INT,
                    status VARCHAR(20) NOT NULL,
                    input_data LONGTEXT,
                    output_data LONGTEXT,
                    error_text TEXT,
                    started_at DATETIME(6) NOT NULL,
                    ended_at DATETIME(6),
                    duration_ms BIGINT DEFAULT 0,
                    created_at DATETIME(6) NOT NULL,
                    INDEX idx_span_trace (trace_id, id),
                    CONSTRAINT fk_span_trace FOREIGN KEY (trace_id) REFERENCES trace_runs(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
            ]

            await cur.execute("SHOW TABLES")
            existing_tables = {row[0] for row in await cur.fetchall()}
            for sql in statements:
                table_match = re.search(r"CREATE TABLE IF NOT EXISTS\s+([a-zA-Z0-9_]+)", sql)
                if table_match and table_match.group(1) in existing_tables:
                    continue
                await cur.execute(sql)

            await cur.execute("SET sql_notes = 1")

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
