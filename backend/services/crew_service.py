"""Crew, membership and Task persistence."""
from datetime import datetime
from typing import Dict, List, Optional

from ..database import execute, execute_many, fetch_all, fetch_one
from .agent_service import get_agent


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def list_crews(user_id: int) -> List[Dict]:
    return await fetch_all(
        "SELECT c.*, a.name AS manager_name, "
        "(SELECT COUNT(*) FROM crew_agents ca WHERE ca.crew_id=c.id) AS agent_count, "
        "(SELECT COUNT(*) FROM crew_tasks ct WHERE ct.crew_id=c.id) AS task_count "
        "FROM crews c LEFT JOIN agents a ON a.id=c.manager_agent_id "
        "WHERE c.user_id=%s ORDER BY c.updated_at DESC",
        (user_id,),
    )


async def _load_task(task: Dict) -> Dict:
    task["dependency_ids"] = [
        row["depends_on_task_id"]
        for row in await fetch_all(
            "SELECT depends_on_task_id FROM task_dependencies WHERE task_id=%s",
            (task["id"],),
        )
    ]
    task["skill_ids"] = [
        row["skill_id"]
        for row in await fetch_all("SELECT skill_id FROM task_skills WHERE task_id=%s", (task["id"],))
    ]
    task["mcp_ids"] = [
        row["mcp_id"]
        for row in await fetch_all("SELECT mcp_id FROM task_mcps WHERE task_id=%s", (task["id"],))
    ]
    return task


async def get_crew(crew_id: int, user_id: int, runtime: bool = False) -> Optional[Dict]:
    crew = await fetch_one("SELECT * FROM crews WHERE id=%s AND user_id=%s", (crew_id, user_id))
    if not crew:
        return None
    member_rows = await fetch_all(
        "SELECT a.id, a.name, a.description, a.role, a.goal, a.model, a.enabled "
        "FROM agents a JOIN crew_agents ca ON a.id=ca.agent_id "
        "WHERE ca.crew_id=%s ORDER BY a.name",
        (crew_id,),
    )
    crew["agents"] = member_rows
    tasks = await fetch_all(
        "SELECT t.*, a.name AS agent_name FROM crew_tasks t "
        "LEFT JOIN agents a ON a.id=t.agent_id WHERE t.crew_id=%s ORDER BY t.order_no, t.id",
        (crew_id,),
    )
    crew["tasks"] = [await _load_task(task) for task in tasks]
    if runtime:
        runtime_agents = []
        for row in member_rows:
            full_agent = await get_agent(row["id"], user_id)
            if full_agent:
                runtime_agents.append(full_agent)
        crew["agents"] = runtime_agents
    return crew


async def _validate_crew(user_id: int, data: Dict) -> List[int]:
    agent_ids = list(dict.fromkeys(data.get("agent_ids", [])))
    if not agent_ids:
        raise ValueError("Crew 至少需要一个 Agent")
    placeholders = ",".join(["%s"] * len(agent_ids))
    rows = await fetch_all(
        f"SELECT id FROM agents WHERE user_id=%s AND enabled=1 AND id IN ({placeholders})",
        (user_id, *agent_ids),
    )
    if {row["id"] for row in rows} != set(agent_ids):
        raise ValueError("Crew 成员包含不存在、禁用或无权访问的 Agent")
    process = data.get("process", "sequential")
    manager_id = data.get("manager_agent_id")
    if process == "hierarchical" and manager_id not in agent_ids:
        raise ValueError("层级流程必须从 Crew 成员中选择 Manager Agent")
    if process == "hierarchical" and len(agent_ids) < 2:
        raise ValueError("层级流程至少需要一个 Manager 和一个协作 Agent")
    tasks = data.get("tasks", [])
    task_keys = [str(task.get("client_key") or task.get("id") or index) for index, task in enumerate(tasks, 1)]
    if len(task_keys) != len(set(task_keys)):
        raise ValueError("Task client_key 不能重复")
    position_by_key = {key: index for index, key in enumerate(task_keys)}
    for index, task in enumerate(tasks):
        task_agent_id = task.get("agent_id")
        if task_agent_id is not None and task_agent_id not in agent_ids:
            raise ValueError(f"Task“{task.get('name', '')}”的负责 Agent 不属于当前 Crew")
        if process == "sequential" and task_agent_id is None:
            raise ValueError(f"顺序流程必须为 Task“{task.get('name', '')}”指定 Agent")
        if process == "hierarchical" and task_agent_id == manager_id:
            raise ValueError(f"Task“{task.get('name', '')}”不能直接分配给 Manager Agent")
        dependencies = [str(key) for key in task.get("dependency_keys", [])]
        if any(key not in position_by_key for key in dependencies):
            raise ValueError(f"Task“{task.get('name', '')}”引用了不存在的依赖")
        if any(position_by_key[key] >= index for key in dependencies):
            raise ValueError(f"Task“{task.get('name', '')}”只能依赖排在它之前的 Task")
        if (task.get("skill_ids") or task.get("mcp_ids")) and task_agent_id is None:
            raise ValueError(f"Task“{task.get('name', '')}”未指定 Agent，不能配置能力白名单")
        if task_agent_id is not None:
            for ids_field, relation_table, id_column in (
                ("skill_ids", "agent_skills", "skill_id"),
                ("mcp_ids", "agent_mcps", "mcp_id"),
            ):
                selected_ids = set(task.get(ids_field) or [])
                if not selected_ids:
                    continue
                relation_rows = await fetch_all(
                    f"SELECT {id_column} AS id FROM {relation_table} WHERE agent_id=%s",
                    (task_agent_id,),
                )
                if not selected_ids.issubset({row["id"] for row in relation_rows}):
                    raise ValueError(f"Task“{task.get('name', '')}”的 {ids_field} 不属于负责 Agent")
    return agent_ids


async def _save_relations(crew_id: int, data: Dict, agent_ids: List[int]) -> None:
    await execute_many(
        "INSERT INTO crew_agents (crew_id, agent_id) VALUES (%s, %s)",
        [(crew_id, agent_id) for agent_id in agent_ids],
    )
    task_ids: Dict[str, int] = {}
    for order, task in enumerate(data.get("tasks", []), start=1):
        task_id = await execute(
            "INSERT INTO crew_tasks (crew_id, name, description, expected_output, agent_id, "
            "order_no, async_execution, human_input, markdown, guardrail, max_retries, "
            "output_file, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, "
            "%s, %s, %s, %s, %s, %s)",
            (
                crew_id,
                task.get("name") or f"Task {order}",
                task.get("description") or "处理用户输入：{{ user_input }}",
                task.get("expected_output") or "完整、准确的结果",
                task.get("agent_id"),
                task.get("order_no", order),
                bool(task.get("async_execution", False)),
                bool(task.get("human_input", False)),
                bool(task.get("markdown", True)),
                task.get("guardrail", ""),
                task.get("max_retries", 2),
                task.get("output_file") or None,
                _now(),
                _now(),
            ),
        )
        key = str(task.get("client_key") or task.get("id") or order)
        task_ids[key] = task_id
        if task.get("skill_ids"):
            await execute_many(
                "INSERT INTO task_skills (task_id, skill_id) VALUES (%s, %s)",
                [(task_id, item_id) for item_id in task["skill_ids"]],
            )
        if task.get("mcp_ids"):
            await execute_many(
                "INSERT INTO task_mcps (task_id, mcp_id) VALUES (%s, %s)",
                [(task_id, item_id) for item_id in task["mcp_ids"]],
            )
    dependency_rows = []
    for order, task in enumerate(data.get("tasks", []), start=1):
        task_key = str(task.get("client_key") or task.get("id") or order)
        for dependency_key in task.get("dependency_keys", []):
            dependency_id = task_ids.get(str(dependency_key))
            if dependency_id and dependency_id != task_ids[task_key]:
                dependency_rows.append((task_ids[task_key], dependency_id))
    if dependency_rows:
        await execute_many(
            "INSERT IGNORE INTO task_dependencies (task_id, depends_on_task_id) VALUES (%s, %s)",
            dependency_rows,
        )


def _crew_values(data: Dict) -> tuple:
    return (
        data.get("name") or "新 Crew",
        data.get("description", ""),
        data.get("process", "sequential"),
        data.get("manager_agent_id"),
        bool(data.get("planning", False)),
        bool(data.get("memory", False)),
        bool(data.get("cache_enabled", False)),
        bool(data.get("verbose", False)),
        data.get("max_rpm"),
        bool(data.get("enabled", True)),
    )


async def create_crew(user_id: int, data: Dict) -> Dict:
    agent_ids = await _validate_crew(user_id, data)
    now = _now()
    crew_id = await execute(
        "INSERT INTO crews (user_id, name, description, process, manager_agent_id, planning, "
        "memory, cache_enabled, verbose, max_rpm, enabled, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (user_id, *_crew_values(data), now, now),
    )
    await _save_relations(crew_id, data, agent_ids)
    return await get_crew(crew_id, user_id)


async def update_crew(crew_id: int, user_id: int, data: Dict) -> Optional[Dict]:
    if not await fetch_one("SELECT id FROM crews WHERE id=%s AND user_id=%s", (crew_id, user_id)):
        return None
    agent_ids = await _validate_crew(user_id, data)
    await execute(
        "UPDATE crews SET name=%s, description=%s, process=%s, manager_agent_id=%s, "
        "planning=%s, memory=%s, cache_enabled=%s, verbose=%s, max_rpm=%s, enabled=%s, "
        "updated_at=%s WHERE id=%s",
        (*_crew_values(data), _now(), crew_id),
    )
    await execute("DELETE FROM crew_tasks WHERE crew_id=%s", (crew_id,))
    await execute("DELETE FROM crew_agents WHERE crew_id=%s", (crew_id,))
    await _save_relations(crew_id, data, agent_ids)
    return await get_crew(crew_id, user_id)


async def delete_crew(crew_id: int, user_id: int) -> bool:
    if not await fetch_one("SELECT id FROM crews WHERE id=%s AND user_id=%s", (crew_id, user_id)):
        return False
    flow_node = await fetch_one(
        "SELECT f.name FROM flows f JOIN flow_nodes n ON n.flow_id=f.id "
        "WHERE n.crew_id=%s AND f.user_id=%s LIMIT 1",
        (crew_id, user_id),
    )
    if flow_node:
        raise ValueError(f"Crew 正在被 Flow“{flow_node['name']}”使用，请先修改或删除该 Flow")
    await execute("DELETE FROM chat_sessions WHERE target_type='crew' AND target_id=%s AND user_id=%s", (crew_id, user_id))
    await execute("DELETE FROM crews WHERE id=%s AND user_id=%s", (crew_id, user_id))
    return True
