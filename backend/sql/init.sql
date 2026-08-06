-- ============================================================
-- Agent Platform 数据库初始化脚本
-- 数据库: MySQL 8.0+ / MariaDB 10.5+
-- 字符集: utf8mb4
-- 引擎: InnoDB
-- ============================================================

CREATE DATABASE IF NOT EXISTS agent_platform
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE agent_platform;

-- ============================================================
-- 用户表
-- ============================================================
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS chat_sessions;
DROP TABLE IF EXISTS agent_mcps;
DROP TABLE IF EXISTS agent_skills;
DROP TABLE IF EXISTS mcp_configs;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS agents;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    password    VARCHAR(100) NOT NULL,
    created_at  DATETIME     NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

INSERT INTO users (username, password, created_at) VALUES ('admin', '123456', NOW());
INSERT INTO users (username, password, created_at) VALUES ('test',  '123456', NOW());

-- ============================================================
-- Agent 表
-- ============================================================
CREATE TABLE agents (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    name        VARCHAR(200) NOT NULL,
    description TEXT,
    system_prompt TEXT,
    model       VARCHAR(100) DEFAULT 'deepseek-chat',
    temperature FLOAT        DEFAULT 0.7,
    iteration_count INT      NOT NULL DEFAULT 6 COMMENT '单次对话最大工具调用迭代次数',
    created_at  DATETIME     NOT NULL,
    updated_at  DATETIME     NOT NULL,
    INDEX       idx_user (user_id),
    CONSTRAINT  fk_agent_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent表';

-- ============================================================
-- Skill 表
-- ============================================================
CREATE TABLE skills (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    name        VARCHAR(200) NOT NULL,
    description TEXT,
    content     TEXT         NOT NULL,
    created_at  DATETIME     NOT NULL,
    INDEX       idx_user (user_id),
    CONSTRAINT  fk_skill_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Skill表';

-- ============================================================
-- MCP 配置表
-- ============================================================
CREATE TABLE mcp_configs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    name        VARCHAR(200) NOT NULL,
    base_url    VARCHAR(500) NOT NULL,
    endpoint    VARCHAR(100) DEFAULT '/mcp',
    description TEXT,
    created_at  DATETIME     NOT NULL,
    INDEX       idx_user (user_id),
    CONSTRAINT  fk_mcp_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='MCP配置表';

-- ============================================================
-- Agent-Skill 关联表
-- ============================================================
CREATE TABLE agent_skills (
    agent_id    INT NOT NULL,
    skill_id    INT NOT NULL,
    PRIMARY KEY (agent_id, skill_id),
    INDEX       idx_skill (skill_id),
    CONSTRAINT  fk_as_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    CONSTRAINT  fk_as_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent-Skill关联表';

-- ============================================================
-- Agent-MCP 关联表
-- ============================================================
CREATE TABLE agent_mcps (
    agent_id    INT NOT NULL,
    mcp_id      INT NOT NULL,
    PRIMARY KEY (agent_id, mcp_id),
    INDEX       idx_mcp (mcp_id),
    CONSTRAINT  fk_am_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    CONSTRAINT  fk_am_mcp   FOREIGN KEY (mcp_id) REFERENCES mcp_configs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent-MCP关联表';

-- ============================================================
-- 会话表
-- ============================================================
CREATE TABLE chat_sessions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    agent_id    INT          NOT NULL,
    title       VARCHAR(200) DEFAULT '新对话',
    created_at  DATETIME     NOT NULL,
    updated_at  DATETIME     NOT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX       idx_user (user_id),
    INDEX       idx_agent (agent_id),
    CONSTRAINT  fk_session_user  FOREIGN KEY (user_id)  REFERENCES users(id),
    CONSTRAINT  fk_session_agent FOREIGN KEY (agent_id) REFERENCES agents(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话表';

-- ============================================================
-- 消息表
-- ============================================================
CREATE TABLE chat_messages (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    session_id  INT    NOT NULL,
    role        VARCHAR(20)  NOT NULL,
    content     TEXT         NOT NULL,
    created_at  DATETIME     NOT NULL,
    INDEX       idx_session (session_id),
    CONSTRAINT  fk_msg_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息表';
