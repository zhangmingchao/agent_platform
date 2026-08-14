-- Agent Platform / CrewAI full reset schema.
-- WARNING: this script intentionally deletes all existing application data.

CREATE DATABASE IF NOT EXISTS agent_platform
    DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE agent_platform;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS trace_spans;
DROP TABLE IF EXISTS trace_runs;
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS chat_sessions;
DROP TABLE IF EXISTS flow_edges;
DROP TABLE IF EXISTS flow_nodes;
DROP TABLE IF EXISTS flows;
DROP TABLE IF EXISTS task_mcps;
DROP TABLE IF EXISTS task_skills;
DROP TABLE IF EXISTS task_dependencies;
DROP TABLE IF EXISTS crew_tasks;
DROP TABLE IF EXISTS crew_agents;
DROP TABLE IF EXISTS crews;
DROP TABLE IF EXISTS agent_delegates;
DROP TABLE IF EXISTS agent_mcps;
DROP TABLE IF EXISTS agent_skills;
DROP TABLE IF EXISTS mcp_configs;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS agents;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE agents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    role VARCHAR(200) NOT NULL DEFAULT 'AI Agent',
    goal TEXT,
    backstory TEXT,
    system_prompt TEXT,
    model VARCHAR(100) NOT NULL DEFAULT 'deepseek-chat',
    temperature FLOAT NOT NULL DEFAULT 0.7,
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    content LONGTEXT NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_skill_user (user_id),
    CONSTRAINT fk_skill_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE mcp_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    endpoint VARCHAR(100) NOT NULL DEFAULT '/mcp',
    description TEXT,
    created_at DATETIME NOT NULL,
    INDEX idx_mcp_user (user_id),
    CONSTRAINT fk_mcp_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE agent_skills (
    agent_id INT NOT NULL,
    skill_id INT NOT NULL,
    PRIMARY KEY (agent_id, skill_id),
    CONSTRAINT fk_as_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    CONSTRAINT fk_as_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE agent_mcps (
    agent_id INT NOT NULL,
    mcp_id INT NOT NULL,
    PRIMARY KEY (agent_id, mcp_id),
    CONSTRAINT fk_am_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    CONSTRAINT fk_am_mcp FOREIGN KEY (mcp_id) REFERENCES mcp_configs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE crews (
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
    CONSTRAINT fk_crew_manager FOREIGN KEY (manager_agent_id) REFERENCES agents(id) ON DELETE SET NULL,
    CHECK (process IN ('sequential', 'hierarchical'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE crew_agents (
    crew_id INT NOT NULL,
    agent_id INT NOT NULL,
    PRIMARY KEY (crew_id, agent_id),
    CONSTRAINT fk_ca_crew FOREIGN KEY (crew_id) REFERENCES crews(id) ON DELETE CASCADE,
    CONSTRAINT fk_ca_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE crew_tasks (
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
    CONSTRAINT fk_task_crew FOREIGN KEY (crew_id) REFERENCES crews(id) ON DELETE CASCADE,
    CONSTRAINT fk_task_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE task_dependencies (
    task_id INT NOT NULL,
    depends_on_task_id INT NOT NULL,
    PRIMARY KEY (task_id, depends_on_task_id),
    CONSTRAINT fk_td_task FOREIGN KEY (task_id) REFERENCES crew_tasks(id) ON DELETE CASCADE,
    CONSTRAINT fk_td_dependency FOREIGN KEY (depends_on_task_id) REFERENCES crew_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE task_skills (
    task_id INT NOT NULL,
    skill_id INT NOT NULL,
    PRIMARY KEY (task_id, skill_id),
    CONSTRAINT fk_ts_task FOREIGN KEY (task_id) REFERENCES crew_tasks(id) ON DELETE CASCADE,
    CONSTRAINT fk_ts_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE task_mcps (
    task_id INT NOT NULL,
    mcp_id INT NOT NULL,
    PRIMARY KEY (task_id, mcp_id),
    CONSTRAINT fk_tm_task FOREIGN KEY (task_id) REFERENCES crew_tasks(id) ON DELETE CASCADE,
    CONSTRAINT fk_tm_mcp FOREIGN KEY (mcp_id) REFERENCES mcp_configs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE flows (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE flow_nodes (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE flow_edges (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE chat_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    target_type VARCHAR(20) NOT NULL,
    target_id INT NOT NULL,
    title VARCHAR(200) NOT NULL DEFAULT '新对话',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_session_user (user_id),
    INDEX idx_session_target (target_type, target_id),
    CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES users(id),
    CHECK (target_type IN ('crew', 'flow'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    role VARCHAR(20) NOT NULL,
    content LONGTEXT NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_message_session (session_id),
    CONSTRAINT fk_msg_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE trace_runs (
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
    CONSTRAINT fk_trace_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_trace_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE trace_spans (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO users (username, password, created_at) VALUES
('admin', '123456', NOW()),
('test', '123456', NOW());
