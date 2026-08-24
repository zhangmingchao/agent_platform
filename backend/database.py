"""
数据库层 —— 基于 aiomysql 的 MySQL 异步操作。
数据表：users, models, agents, agent_skills, agent_mcps, skills, mcp_configs,
        chat_sessions, chat_messages, trace_runs, trace_spans
"""
import aiomysql
import logging
from datetime import datetime
from typing import Optional, List, Dict

from .config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

log = logging.getLogger("agent-platform")

_pool: Optional[aiomysql.Pool] = None


async def _ensure_database_exists():
    conn = await aiomysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD
    )
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "CREATE DATABASE IF NOT EXISTS `%s` DEFAULT CHARACTER SET utf8mb4" % DB_NAME
            )
        log.info("[DB] database '%s' ensured", DB_NAME)
    finally:
        conn.close()


async def get_pool() -> aiomysql.Pool:
    global _pool
    if _pool is None:
        await _ensure_database_exists()
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
            statements = [
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
                    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
                    password VARCHAR(100) NOT NULL COMMENT '登录密码',
                    created_at DATETIME NOT NULL COMMENT '创建时间'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表'
                """,
                """
                CREATE TABLE IF NOT EXISTS models (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '模型配置ID',
                    user_id INT NOT NULL COMMENT '所属用户ID',
                    name VARCHAR(100) NOT NULL COMMENT '配置名称',
                    provider VARCHAR(50) DEFAULT 'openai' COMMENT '模型提供商 openai/deepseek/anthropic/qwen',
                    model_id VARCHAR(100) NOT NULL COMMENT '模型标识 如 gpt-4o / deepseek-chat',
                    api_key VARCHAR(500) NOT NULL COMMENT 'API 密钥',
                    base_url VARCHAR(500) DEFAULT '' COMMENT 'API 基础地址',
                    temperature FLOAT DEFAULT 0.7 COMMENT '采样温度 0-2',
                    max_tokens INT DEFAULT 4096 COMMENT '最大生成 token 数',
                    is_active TINYINT DEFAULT 1 COMMENT '是否启用 1启用 0禁用',
                    created_at DATETIME NOT NULL COMMENT '创建时间',
                    updated_at DATETIME NOT NULL COMMENT '更新时间',
                    INDEX idx_user (user_id),
                    CONSTRAINT fk_model_user FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模型配置表（用户级）'
                """,
                """
                CREATE TABLE IF NOT EXISTS agents (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Agent ID',
                    user_id INT NOT NULL COMMENT '所属用户ID',
                    name VARCHAR(200) NOT NULL COMMENT 'Agent 名称',
                    description TEXT COMMENT 'Agent 描述',
                    system_prompt TEXT COMMENT '系统提示词',
                    model VARCHAR(100) DEFAULT 'deepseek-chat' COMMENT '内置模型标识',
                    model_config_id INT DEFAULT NULL COMMENT '自定义模型配置ID 关联 models.id',
                    temperature FLOAT DEFAULT 0.7 COMMENT '采样温度 0-2',
                    iteration_count INT NOT NULL DEFAULT 6 COMMENT '最大工具迭代次数',
                    created_at DATETIME NOT NULL COMMENT '创建时间',
                    updated_at DATETIME NOT NULL COMMENT '更新时间',
                    INDEX idx_user (user_id),
                    CONSTRAINT fk_agent_user FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent 智能体表'
                """,
                """
                CREATE TABLE IF NOT EXISTS skills (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Skill ID',
                    user_id INT NOT NULL COMMENT '所属用户ID',
                    name VARCHAR(200) NOT NULL COMMENT 'Skill 名称',
                    description TEXT COMMENT 'Skill 描述',
                    content TEXT NOT NULL COMMENT 'Skill 内容（JSON 格式）',
                    created_at DATETIME NOT NULL COMMENT '创建时间',
                    INDEX idx_user (user_id),
                    CONSTRAINT fk_skill_user FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Skill 技能表'
                """,
                """
                CREATE TABLE IF NOT EXISTS mcp_configs (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'MCP 配置ID',
                    user_id INT NOT NULL COMMENT '所属用户ID',
                    name VARCHAR(200) NOT NULL COMMENT 'MCP 服务器名称',
                    base_url VARCHAR(500) NOT NULL COMMENT 'MCP 服务器地址',
                    endpoint VARCHAR(100) DEFAULT '/mcp' COMMENT 'MCP SSE 端点路径',
                    description TEXT COMMENT 'MCP 描述',
                    created_at DATETIME NOT NULL COMMENT '创建时间',
                    INDEX idx_user (user_id),
                    CONSTRAINT fk_mcp_user FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='MCP 配置表'
                """,
                """
                CREATE TABLE IF NOT EXISTS agent_skills (
                    agent_id INT NOT NULL COMMENT 'Agent ID',
                    skill_id INT NOT NULL COMMENT 'Skill ID',
                    PRIMARY KEY (agent_id, skill_id),
                    INDEX idx_skill (skill_id),
                    CONSTRAINT fk_as_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                    CONSTRAINT fk_as_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent-Skill 关联表'
                """,
                """
                CREATE TABLE IF NOT EXISTS agent_mcps (
                    agent_id INT NOT NULL COMMENT 'Agent ID',
                    mcp_id INT NOT NULL COMMENT 'MCP 配置ID',
                    PRIMARY KEY (agent_id, mcp_id),
                    INDEX idx_mcp (mcp_id),
                    CONSTRAINT fk_am_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                    CONSTRAINT fk_am_mcp FOREIGN KEY (mcp_id) REFERENCES mcp_configs(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent-MCP 关联表'
                """,
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '会话ID',
                    user_id INT NOT NULL COMMENT '所属用户ID',
                    agent_id INT NOT NULL COMMENT '关联 Agent ID',
                    title VARCHAR(200) DEFAULT '新对话' COMMENT '会话标题',
                    created_at DATETIME NOT NULL COMMENT '创建时间',
                    updated_at DATETIME NOT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '最后活跃时间',
                    INDEX idx_user (user_id),
                    INDEX idx_agent (agent_id),
                    CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES users(id),
                    CONSTRAINT fk_session_agent FOREIGN KEY (agent_id) REFERENCES agents(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天会话表'
                """,
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '消息ID',
                    session_id INT NOT NULL COMMENT '会话ID',
                    role VARCHAR(20) NOT NULL COMMENT '角色 user/assistant',
                    content TEXT NOT NULL COMMENT '消息内容',
                    attachments JSON DEFAULT NULL COMMENT '附件列表（图片 base64 等）',
                    created_at DATETIME NOT NULL COMMENT '发送时间',
                    INDEX idx_session (session_id),
                    CONSTRAINT fk_msg_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天消息表'
                """,
                """
                CREATE TABLE IF NOT EXISTS trace_runs (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Trace 运行ID',
                    session_id INT COMMENT '聊天会话ID（单聊时）',
                    user_id INT NOT NULL COMMENT '所属用户ID',
                    agent_id INT NOT NULL COMMENT 'Agent ID',
                    workflow_run_id INT DEFAULT NULL COMMENT '工作流运行ID（工作流场景）',
                    workflow_step_id INT DEFAULT NULL COMMENT '工作流步骤ID（工作流场景）',
                    status VARCHAR(20) DEFAULT 'running' COMMENT '运行状态 running/success/error/cancelled',
                    input_text TEXT COMMENT '输入文本',
                    output_text TEXT COMMENT '输出文本',
                    error_text TEXT COMMENT '错误信息',
                    model VARCHAR(100) COMMENT '使用的模型名称',
                    total_tokens INT DEFAULT 0 COMMENT '总 token 消耗',
                    total_duration_ms INT DEFAULT 0 COMMENT '总耗时（毫秒）',
                    started_at DATETIME NOT NULL COMMENT '开始时间',
                    created_at DATETIME NOT NULL COMMENT '创建时间',
                    INDEX idx_session (session_id),
                    INDEX idx_user (user_id),
                    INDEX idx_workflow_run (workflow_run_id),
                    INDEX idx_workflow_step (workflow_step_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Trace 调用链运行记录表'
                """,
                """
                CREATE TABLE IF NOT EXISTS trace_spans (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Span ID',
                    run_id INT NOT NULL COMMENT '所属 Trace 运行ID',
                    span_type VARCHAR(50) NOT NULL COMMENT '类型 llm/tool',
                    name VARCHAR(200) COMMENT '模型名称或工具名称',
                    round_no INT DEFAULT NULL COMMENT '第几次工具调用轮次',
                    input_data TEXT COMMENT '输入数据',
                    output_data TEXT COMMENT '输出数据',
                    error_text TEXT COMMENT '错误信息',
                    tokens_used INT DEFAULT 0 COMMENT '消耗 token 数',
                    duration_ms INT DEFAULT 0 COMMENT '耗时（毫秒）',
                    status VARCHAR(20) DEFAULT 'running' COMMENT '状态 running/success/error',
                    started_at DATETIME NOT NULL COMMENT '开始时间',
                    created_at DATETIME NOT NULL COMMENT '创建时间',
                    INDEX idx_run (run_id),
                    CONSTRAINT fk_span_run FOREIGN KEY (run_id) REFERENCES trace_runs(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Trace Span 明细表'
                """,
                """
                CREATE TABLE IF NOT EXISTS multi_agent_workflows (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '工作流ID',
                    user_id INT NOT NULL COMMENT '所属用户ID',
                    name VARCHAR(200) NOT NULL COMMENT '工作流名称',
                    description TEXT COMMENT '工作流描述',
                    mode VARCHAR(50) DEFAULT 'sequential' COMMENT '执行模式 sequential/dag',
                    config_json JSON NOT NULL COMMENT '工作流配置（steps 或 nodes+edges）',
                    is_active TINYINT DEFAULT 1 COMMENT '是否启用 1启用 0禁用',
                    created_at DATETIME NOT NULL COMMENT '创建时间',
                    updated_at DATETIME NOT NULL COMMENT '更新时间',
                    INDEX idx_user (user_id),
                    CONSTRAINT fk_workflow_user FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='多 Agent 工作流定义表'
                """,
                """
                CREATE TABLE IF NOT EXISTS multi_agent_runs (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '工作流运行ID',
                    workflow_id INT NOT NULL COMMENT '工作流ID',
                    user_id INT NOT NULL COMMENT '所属用户ID',
                    status VARCHAR(20) DEFAULT 'running' COMMENT '运行状态 running/success/error',
                    current_node_id VARCHAR(100) DEFAULT NULL COMMENT '当前执行节点ID（DAG 模式）',
                    context_json JSON DEFAULT NULL COMMENT '运行上下文数据',
                    input_text TEXT COMMENT '工作流输入',
                    output_text TEXT COMMENT '工作流输出',
                    error_text TEXT COMMENT '错误信息',
                    started_at DATETIME NOT NULL COMMENT '开始时间',
                    finished_at DATETIME DEFAULT NULL COMMENT '结束时间',
                    created_at DATETIME NOT NULL COMMENT '创建时间',
                    INDEX idx_workflow (workflow_id),
                    INDEX idx_user (user_id),
                    CONSTRAINT fk_run_workflow FOREIGN KEY (workflow_id) REFERENCES multi_agent_workflows(id) ON DELETE CASCADE,
                    CONSTRAINT fk_run_user FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='多 Agent 工作流运行记录表'
                """,
                """
                CREATE TABLE IF NOT EXISTS multi_agent_run_steps (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '步骤ID',
                    run_id INT NOT NULL COMMENT '工作流运行ID',
                    step_order INT NOT NULL COMMENT '步骤顺序',
                    agent_id INT DEFAULT NULL COMMENT '执行的 Agent ID',
                    trace_run_id INT DEFAULT NULL COMMENT '关联 Trace 运行ID',
                    node_id VARCHAR(100) DEFAULT NULL COMMENT 'DAG 节点ID（DAG 模式）',
                    node_type VARCHAR(50) DEFAULT NULL COMMENT 'DAG 节点类型 agent/condition/parallel/input/output',
                    role_name VARCHAR(100) COMMENT '步骤角色名称',
                    instruction TEXT COMMENT '步骤指令',
                    input_text TEXT COMMENT '步骤输入',
                    output_text TEXT COMMENT '步骤输出',
                    status VARCHAR(20) DEFAULT 'running' COMMENT '状态 running/success/error',
                    error_text TEXT COMMENT '错误信息',
                    started_at DATETIME NOT NULL COMMENT '开始时间',
                    finished_at DATETIME DEFAULT NULL COMMENT '结束时间',
                    created_at DATETIME NOT NULL COMMENT '创建时间',
                    INDEX idx_run (run_id),
                    INDEX idx_trace_run (trace_run_id),
                    CONSTRAINT fk_run_step_run FOREIGN KEY (run_id) REFERENCES multi_agent_runs(id) ON DELETE CASCADE,
                    CONSTRAINT fk_run_step_agent FOREIGN KEY (agent_id) REFERENCES agents(id),
                    CONSTRAINT fk_run_step_trace FOREIGN KEY (trace_run_id) REFERENCES trace_runs(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='多 Agent 工作流执行步骤表'
                """,
                """
                CREATE TABLE IF NOT EXISTS runtime_files (
                    id VARCHAR(36) PRIMARY KEY COMMENT '文件逻辑ID',
                    user_id INT NOT NULL COMMENT '所属用户ID',
                    session_id INT DEFAULT NULL COMMENT '关联会话ID',
                    execution_id VARCHAR(36) DEFAULT NULL COMMENT '产出该文件的执行ID',
                    file_name VARCHAR(200) NOT NULL COMMENT '文件名',
                    storage_path VARCHAR(1000) NOT NULL COMMENT '服务端存储路径',
                    mime_type VARCHAR(200) DEFAULT NULL COMMENT 'MIME 类型',
                    size_bytes BIGINT NOT NULL COMMENT '文件字节数',
                    sha256 VARCHAR(64) NOT NULL COMMENT '文件摘要',
                    file_type VARCHAR(20) NOT NULL COMMENT '类型 input/artifact',
                    created_at DATETIME NOT NULL COMMENT '创建时间',
                    INDEX idx_runtime_files_user (user_id),
                    INDEX idx_runtime_files_session (session_id),
                    INDEX idx_runtime_files_execution (execution_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Python Runtime 文件表'
                """,
                """
                CREATE TABLE IF NOT EXISTS code_executions (
                    id VARCHAR(36) PRIMARY KEY COMMENT '执行ID',
                    user_id INT NOT NULL COMMENT '所属用户ID',
                    session_id INT DEFAULT NULL COMMENT '关联会话ID',
                    workflow_run_id INT DEFAULT NULL COMMENT '工作流运行ID',
                    workflow_step_id INT DEFAULT NULL COMMENT '工作流步骤ID',
                    node_id VARCHAR(100) DEFAULT NULL COMMENT '节点ID',
                    source_type VARCHAR(30) NOT NULL COMMENT '来源 generated_code/skill_script',
                    skill_id INT DEFAULT NULL COMMENT 'Skill ID',
                    code_sha256 VARCHAR(64) NOT NULL COMMENT '代码摘要',
                    status VARCHAR(20) NOT NULL COMMENT '执行状态',
                    timeout_seconds INT NOT NULL COMMENT '超时秒数',
                    exit_code INT DEFAULT NULL COMMENT '子进程退出码',
                    stdout_text MEDIUMTEXT DEFAULT NULL COMMENT '标准输出',
                    stderr_text MEDIUMTEXT DEFAULT NULL COMMENT '错误输出',
                    result_json JSON DEFAULT NULL COMMENT '结构化结果',
                    error_text TEXT DEFAULT NULL COMMENT '错误信息',
                    started_at DATETIME DEFAULT NULL COMMENT '开始时间',
                    finished_at DATETIME DEFAULT NULL COMMENT '结束时间',
                    created_at DATETIME NOT NULL COMMENT '创建时间',
                    INDEX idx_code_executions_user (user_id),
                    INDEX idx_code_executions_session (session_id),
                    INDEX idx_code_executions_workflow_run (workflow_run_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Python Runtime 执行记录表'
                """,
            ]

            for sql in statements:
                await cur.execute(sql)

            # 数据迁移：如果 agents 表缺少 model_config_id 字段则添加
            try:
                await cur.execute(
                    "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='agents' AND COLUMN_NAME='model_config_id'",
                    (DB_NAME,)
                )
                if not await cur.fetchone():
                    await cur.execute(
                        "ALTER TABLE agents ADD COLUMN model_config_id INT DEFAULT NULL AFTER model"
                    )
                    log.info("[DB] added model_config_id column to agents table")
            except Exception:
                pass

            migrations = [
                (
                    "trace_runs",
                    "workflow_run_id",
                    "ALTER TABLE trace_runs ADD COLUMN workflow_run_id INT DEFAULT NULL AFTER agent_id",
                ),
                (
                    "trace_runs",
                    "workflow_step_id",
                    "ALTER TABLE trace_runs ADD COLUMN workflow_step_id INT DEFAULT NULL AFTER workflow_run_id",
                ),
                (
                    "multi_agent_run_steps",
                    "trace_run_id",
                    "ALTER TABLE multi_agent_run_steps ADD COLUMN trace_run_id INT DEFAULT NULL AFTER agent_id",
                ),
                (
                    "multi_agent_runs",
                    "current_node_id",
                    "ALTER TABLE multi_agent_runs ADD COLUMN current_node_id VARCHAR(100) DEFAULT NULL AFTER status",
                ),
                (
                    "multi_agent_runs",
                    "context_json",
                    "ALTER TABLE multi_agent_runs ADD COLUMN context_json JSON DEFAULT NULL AFTER current_node_id",
                ),
                (
                    "multi_agent_run_steps",
                    "node_id",
                    "ALTER TABLE multi_agent_run_steps ADD COLUMN node_id VARCHAR(100) DEFAULT NULL AFTER agent_id",
                ),
                (
                    "multi_agent_run_steps",
                    "node_type",
                    "ALTER TABLE multi_agent_run_steps ADD COLUMN node_type VARCHAR(50) DEFAULT NULL AFTER node_id",
                ),
                (
                    "chat_messages",
                    "attachments",
                    "ALTER TABLE chat_messages ADD COLUMN attachments JSON DEFAULT NULL AFTER content",
                ),
            ]
            for table_name, column_name, alter_sql in migrations:
                try:
                    await cur.execute(
                        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s",
                        (DB_NAME, table_name, column_name),
                    )
                    if not await cur.fetchone():
                        await cur.execute(alter_sql)
                        log.info("[DB] added %s column to %s table", column_name, table_name)
                except Exception:
                    pass

            # 数据迁移：将 multi_agent_run_steps 中的 agent_id 改为可空
            try:
                await cur.execute(
                    "SELECT IS_NULLABLE FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='multi_agent_run_steps' AND COLUMN_NAME='agent_id'",
                    (DB_NAME,)
                )
                row = await cur.fetchone()
                if row and row[0] == 'NO':
                    await cur.execute(
                        "ALTER TABLE multi_agent_run_steps MODIFY COLUMN agent_id INT DEFAULT NULL"
                    )
                    log.info("[DB] modified agent_id to allow NULL in multi_agent_run_steps")
            except Exception:
                pass

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
            log.info("[DB] initialized (agent_platform_langchain), default users: admin/123456, test/123456")
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
        # autocommit=False 时，普通 SELECT 也会开启事务。在连接归还连接池之前
        # 必须结束该事务，否则下一个请求复用连接时可能仍处于旧的一致性快照中，
        # 看不到其他连接刚提交的数据（例如刚创建的 Workflow Run）。
        await conn.rollback()
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
