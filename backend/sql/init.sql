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
    password VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) DEFAULT 'openai',
    model_id VARCHAR(100) NOT NULL,
    api_key VARCHAR(500) NOT NULL,
    base_url VARCHAR(500) DEFAULT '',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INT DEFAULT 4096,
    is_active TINYINT DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_models_user (user_id),
    CONSTRAINT fk_model_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS agents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    system_prompt TEXT,
    model VARCHAR(100) DEFAULT 'deepseek-chat',
    model_config_id INT DEFAULT NULL,
    temperature FLOAT DEFAULT 0.7,
    iteration_count INT NOT NULL DEFAULT 6,
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
    created_at DATETIME NOT NULL,
    INDEX idx_chat_messages_session (session_id),
    CONSTRAINT fk_msg_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS trace_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT DEFAULT NULL,
    user_id INT NOT NULL,
    agent_id INT NOT NULL,
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

INSERT INTO users (username, password, created_at)
VALUES ('admin', '123456', NOW())
ON DUPLICATE KEY UPDATE username = VALUES(username);

INSERT INTO users (username, password, created_at)
VALUES ('test', '123456', NOW())
ON DUPLICATE KEY UPDATE username = VALUES(username);
