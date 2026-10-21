"""插件数据库结构；由应用统一初始化，幂等创建新表。"""

PLUGIN_TABLES = [
    """CREATE TABLE IF NOT EXISTS plugin_configs (
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户插件配置'""",
    """CREATE TABLE IF NOT EXISTS agent_plugins (
        agent_id INT NOT NULL,
        user_id INT NOT NULL,
        plugin_id VARCHAR(100) NOT NULL,
        PRIMARY KEY (agent_id, plugin_id),
        FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id, plugin_id) REFERENCES plugin_configs(user_id, plugin_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent 插件绑定'""",
    """CREATE TABLE IF NOT EXISTS plugin_activity (
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='插件脱敏操作与调用记录'""",
]
