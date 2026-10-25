-- Agent Platform database initialization
-- MySQL 8.0+ / MariaDB 10.5+
-- Non-destructive: existing tables and data are preserved.

CREATE DATABASE IF NOT EXISTS agent_platform_langchain
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE agent_platform_langchain;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL COMMENT 'Argon2id 密码哈希',
    created_at DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_api_keys (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    key_id VARCHAR(32) NOT NULL,
    key_prefix VARCHAR(64) NOT NULL,
    key_hash CHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    last_used_at DATETIME DEFAULT NULL,
    revoked_at DATETIME DEFAULT NULL,
    UNIQUE KEY uk_user_api_key_user (user_id),
    UNIQUE KEY uk_user_api_key_key_id (key_id),
    CONSTRAINT fk_user_api_key_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) DEFAULT 'openai',
    model_id VARCHAR(100) NOT NULL,
    api_key VARCHAR(1024) NOT NULL COMMENT 'AES-256-GCM 加密的 API 密钥',
    base_url VARCHAR(500) DEFAULT '',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INT DEFAULT 4096,
    quota_mode VARCHAR(20) NOT NULL DEFAULT 'unlimited',
    daily_token_limit BIGINT DEFAULT NULL,
    is_active TINYINT DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_models_user (user_id),
    CONSTRAINT fk_model_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS model_daily_token_usage (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    model_config_id INT NOT NULL,
    user_id INT NOT NULL,
    usage_date DATE NOT NULL,
    input_tokens BIGINT NOT NULL DEFAULT 0,
    output_tokens BIGINT NOT NULL DEFAULT 0,
    total_tokens BIGINT NOT NULL DEFAULT 0,
    request_count BIGINT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_model_usage_date (model_config_id, usage_date),
    INDEX idx_model_usage_user_date (user_id, usage_date),
    CONSTRAINT fk_model_usage_model FOREIGN KEY (model_config_id) REFERENCES models(id) ON DELETE CASCADE,
    CONSTRAINT fk_model_usage_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS agents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    system_prompt TEXT,
    prompt_variables JSON DEFAULT NULL,
    output_schema JSON DEFAULT NULL,
    model VARCHAR(100) DEFAULT 'deepseek-chat',
    model_config_id INT DEFAULT NULL,
    temperature FLOAT DEFAULT 0.7,
    iteration_count INT NOT NULL DEFAULT 6,
    execution_timeout_seconds INT NOT NULL DEFAULT 120,
    planning_mode VARCHAR(20) NOT NULL DEFAULT 'disabled',
    permission_preset VARCHAR(30) NOT NULL DEFAULT 'standard',
    allow_delegation BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否允许委托',
    delegation_agent_ids JSON DEFAULT NULL COMMENT '委托目标Agent白名单',
    delegation_max_calls INT NOT NULL DEFAULT 3 COMMENT '每轮最大委托次数',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_agents_user (user_id),
    INDEX idx_agents_model_config (model_config_id),
    CONSTRAINT fk_agent_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_agent_model_config FOREIGN KEY (model_config_id) REFERENCES models(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_skills_user (user_id),
    CONSTRAINT fk_skill_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS mcp_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    endpoint VARCHAR(100) DEFAULT '/mcp',
    timeout_seconds INT NOT NULL DEFAULT 30,
    description TEXT,
    created_at DATETIME NOT NULL,
    INDEX idx_mcp_configs_user (user_id),
    CONSTRAINT fk_mcp_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS agent_skills (
    agent_id INT NOT NULL,
    skill_id INT NOT NULL,
    PRIMARY KEY (agent_id, skill_id),
    INDEX idx_agent_skills_skill (skill_id),
    CONSTRAINT fk_as_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    CONSTRAINT fk_as_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS agent_mcps (
    agent_id INT NOT NULL,
    mcp_id INT NOT NULL,
    PRIMARY KEY (agent_id, mcp_id),
    INDEX idx_agent_mcps_mcp (mcp_id),
    CONSTRAINT fk_am_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    CONSTRAINT fk_am_mcp FOREIGN KEY (mcp_id) REFERENCES mcp_configs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS chat_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    agent_id INT NOT NULL,
    title VARCHAR(200) DEFAULT '新对话',
    permission_preset VARCHAR(30) DEFAULT NULL,
    sandbox_mode VARCHAR(30) DEFAULT NULL,
    approval_policy VARCHAR(20) DEFAULT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_chat_sessions_user (user_id),
    INDEX idx_chat_sessions_agent (agent_id),
    CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_session_agent FOREIGN KEY (agent_id) REFERENCES agents(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    reasoning_content MEDIUMTEXT DEFAULT NULL,
    delegation_results JSON DEFAULT NULL COMMENT '本轮委托状态与公开结果摘要',
    structured_content JSON DEFAULT NULL,
    attachments JSON DEFAULT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_chat_messages_session (session_id),
    CONSTRAINT fk_msg_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS runtime_files (
    id VARCHAR(36) PRIMARY KEY,
    user_id INT NOT NULL,
    session_id INT DEFAULT NULL,
    execution_id VARCHAR(36) DEFAULT NULL,
    file_name VARCHAR(200) NOT NULL,
    storage_path VARCHAR(1000) NOT NULL,
    mime_type VARCHAR(200) DEFAULT NULL,
    size_bytes BIGINT NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_runtime_files_user (user_id),
    INDEX idx_runtime_files_session (session_id),
    INDEX idx_runtime_files_execution (execution_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS code_executions (
    id VARCHAR(36) PRIMARY KEY,
    user_id INT NOT NULL,
    workspace_id VARCHAR(100) NOT NULL DEFAULT 'default',
    session_id INT DEFAULT NULL,
    workflow_run_id INT DEFAULT NULL,
    workflow_step_id INT DEFAULT NULL,
    node_id VARCHAR(100) DEFAULT NULL,
    code_sha256 VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL COMMENT 'queued/running/completed/failed/timed_out/cancelled',
    timeout_seconds INT NOT NULL,
    exit_code INT DEFAULT NULL,
    sandbox_container_id VARCHAR(100) DEFAULT NULL,
    stdout_text MEDIUMTEXT DEFAULT NULL,
    stderr_text MEDIUMTEXT DEFAULT NULL,
    result_json JSON DEFAULT NULL,
    error_text TEXT DEFAULT NULL,
    started_at DATETIME DEFAULT NULL,
    finished_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_code_executions_user (user_id),
    INDEX idx_code_executions_workspace (user_id, workspace_id),
    INDEX idx_code_executions_session (session_id),
    INDEX idx_code_executions_workflow_run (workflow_run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS trace_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_trace_run_id INT DEFAULT NULL COMMENT '委托父Trace ID',
    session_id INT DEFAULT NULL,
    user_id INT NOT NULL,
    agent_id INT NOT NULL,
    invocation_source VARCHAR(20) NOT NULL DEFAULT 'platform',
    request_id VARCHAR(64) DEFAULT NULL,
    client_conversation_id VARCHAR(100) DEFAULT NULL,
    workflow_run_id INT DEFAULT NULL,
    workflow_step_id INT DEFAULT NULL,
    status VARCHAR(20) DEFAULT 'running',
    input_text TEXT,
    output_text TEXT,
    error_text TEXT,
    model VARCHAR(100),
    total_tokens INT DEFAULT 0,
    total_duration_ms INT DEFAULT 0,
    started_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_trace_runs_session (session_id),
    INDEX idx_trace_runs_user (user_id),
    UNIQUE INDEX uk_trace_runs_request_id (request_id),
    INDEX idx_trace_runs_workflow_run (workflow_run_id),
    INDEX idx_trace_runs_workflow_step (workflow_step_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS trace_spans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id INT NOT NULL,
    span_type VARCHAR(50) NOT NULL,
    name VARCHAR(200),
    round_no INT DEFAULT NULL,
    input_data TEXT,
    output_data TEXT,
    error_text TEXT,
    tokens_used INT DEFAULT 0,
    duration_ms INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'running',
    started_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_trace_spans_run (run_id),
    CONSTRAINT fk_span_run FOREIGN KEY (run_id) REFERENCES trace_runs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS session_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id INT DEFAULT NULL,
    trace_run_id INT DEFAULT NULL,
    agent_id INT DEFAULT NULL,
    workflow_run_id INT DEFAULT NULL,
    workflow_step_id INT DEFAULT NULL,
    event_source VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    turn_id VARCHAR(120) DEFAULT '',
    step_id VARCHAR(160) DEFAULT '',
    run_id VARCHAR(120) DEFAULT '',
    phase VARCHAR(80) DEFAULT '',
    name VARCHAR(200) DEFAULT '',
    status VARCHAR(40) DEFAULT '',
    payload_json JSON DEFAULT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_session_events_user_id (user_id, id),
    INDEX idx_session_events_session_id (session_id, id),
    INDEX idx_session_events_trace_run_id (trace_run_id, id),
    CONSTRAINT fk_session_events_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_session_events_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_session_events_trace FOREIGN KEY (trace_run_id) REFERENCES trace_runs(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS agent_task_plans (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    trace_run_id INT NOT NULL,
    user_id INT NOT NULL,
    agent_id INT NOT NULL,
    goal VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    current_step_order INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    finished_at DATETIME DEFAULT NULL,
    UNIQUE KEY uk_agent_task_plan_trace (trace_run_id),
    INDEX idx_agent_task_plan_user (user_id),
    INDEX idx_agent_task_plan_agent (agent_id),
    CONSTRAINT fk_agent_task_plan_trace FOREIGN KEY (trace_run_id) REFERENCES trace_runs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS agent_task_plan_steps (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    plan_id BIGINT NOT NULL,
    step_key VARCHAR(32) NOT NULL,
    step_order INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    instruction TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    result_summary MEDIUMTEXT DEFAULT NULL,
    error_text TEXT DEFAULT NULL,
    started_at DATETIME DEFAULT NULL,
    finished_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_agent_task_plan_step_order (plan_id, step_order),
    UNIQUE KEY uk_agent_task_plan_step_key (plan_id, step_key),
    CONSTRAINT fk_agent_task_plan_step_plan FOREIGN KEY (plan_id) REFERENCES agent_task_plans(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS multi_agent_workflows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    mode VARCHAR(50) DEFAULT 'sequential',
    config_json JSON NOT NULL,
    is_active TINYINT DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_workflows_user (user_id),
    CONSTRAINT fk_workflow_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS multi_agent_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    workflow_id INT NOT NULL,
    user_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'running',
    current_node_id VARCHAR(100) DEFAULT NULL,
    context_json JSON DEFAULT NULL,
    workflow_config_json JSON NOT NULL COMMENT '创建运行时的工作流配置快照',
    input_text TEXT,
    output_text TEXT,
    error_text TEXT,
    started_at DATETIME NOT NULL,
    finished_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_multi_agent_runs_workflow (workflow_id),
    INDEX idx_multi_agent_runs_user (user_id),
    CONSTRAINT fk_run_workflow FOREIGN KEY (workflow_id) REFERENCES multi_agent_workflows(id) ON DELETE CASCADE,
    CONSTRAINT fk_run_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS multi_agent_run_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id INT NOT NULL,
    step_order INT NOT NULL,
    agent_id INT DEFAULT NULL,
    node_id VARCHAR(100) DEFAULT NULL,
    node_type VARCHAR(50) DEFAULT NULL,
    trace_run_id INT DEFAULT NULL,
    role_name VARCHAR(100),
    instruction TEXT,
    input_text TEXT,
    output_text TEXT,
    output_json JSON DEFAULT NULL,
    status VARCHAR(20) DEFAULT 'running',
    error_text TEXT,
    started_at DATETIME NOT NULL,
    finished_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_multi_agent_run_steps_run (run_id),
    INDEX idx_multi_agent_run_steps_trace (trace_run_id),
    INDEX idx_multi_agent_run_steps_agent (agent_id),
    CONSTRAINT fk_run_step_run FOREIGN KEY (run_id) REFERENCES multi_agent_runs(id) ON DELETE CASCADE,
    CONSTRAINT fk_run_step_agent FOREIGN KEY (agent_id) REFERENCES agents(id),
    CONSTRAINT fk_run_step_trace FOREIGN KEY (trace_run_id) REFERENCES trace_runs(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 插件管理结构与 backend/plugins/schema.py 保持一致，应用启动也会幂等创建。
CREATE TABLE IF NOT EXISTS plugin_configs (
    user_id INT NOT NULL COMMENT '配置所属用户',
    plugin_id VARCHAR(100) NOT NULL COMMENT '内置插件唯一标识',
    base_url VARCHAR(500) NOT NULL DEFAULT '',
    encrypted_token TEXT NOT NULL COMMENT '加密后的插件凭据',
    timeout_seconds INT NOT NULL DEFAULT 30,
    max_output_bytes INT NOT NULL DEFAULT 1048576,
    values_json JSON DEFAULT NULL COMMENT '插件声明中的普通配置，NULL 表示旧 BI 结构',
    secrets_json JSON DEFAULT NULL COMMENT '按字段加密的凭据映射，不保存明文',
    enabled TINYINT NOT NULL DEFAULT 0,
    revision INT NOT NULL DEFAULT 1 COMMENT '乐观锁配置版本',
    health_status VARCHAR(20) NOT NULL DEFAULT 'untested',
    health_message VARCHAR(500) NOT NULL DEFAULT '',
    tested_at DATETIME DEFAULT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (user_id, plugin_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户插件配置';

CREATE TABLE IF NOT EXISTS agent_plugins (
    agent_id INT NOT NULL,
    user_id INT NOT NULL,
    plugin_id VARCHAR(100) NOT NULL,
    PRIMARY KEY (agent_id, plugin_id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id, plugin_id) REFERENCES plugin_configs(user_id, plugin_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent 插件绑定';

CREATE TABLE IF NOT EXISTS plugin_activity (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    plugin_id VARCHAR(100) NOT NULL,
    action VARCHAR(40) NOT NULL,
    status VARCHAR(20) NOT NULL,
    message VARCHAR(500) NOT NULL DEFAULT '',
    duration_ms INT NOT NULL DEFAULT 0,
    agent_id INT DEFAULT NULL,
    trace_run_id INT DEFAULT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_plugin_activity_user (user_id, plugin_id, id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='插件脱敏操作与调用记录';

-- 可安装插件版本与持久化执行队列。
CREATE TABLE IF NOT EXISTS plugin_packages (
        user_id INT NOT NULL,
        plugin_id VARCHAR(100) NOT NULL,
        version VARCHAR(100) NOT NULL,
        digest CHAR(64) NOT NULL,
        manifest_json JSON NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'queued',
        active TINYINT NOT NULL DEFAULT 0,
        error_message VARCHAR(500) NOT NULL DEFAULT '',
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        PRIMARY KEY (user_id,plugin_id,version),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户私有插件安装包版本';

CREATE TABLE IF NOT EXISTS plugin_executions (
        id CHAR(32) PRIMARY KEY,
        user_id INT NOT NULL,
        plugin_id VARCHAR(100) NOT NULL,
        version VARCHAR(100) NOT NULL,
        encrypted_request MEDIUMTEXT NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'queued',
        result_json MEDIUMTEXT DEFAULT NULL,
        cancel_requested TINYINT NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        INDEX idx_plugin_execution_owner (user_id,plugin_id,status),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='插件执行与加密配置快照';
