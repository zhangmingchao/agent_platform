"""Persisted Flow graph definitions that orchestrate one or more Crews."""
import json
from datetime import datetime
from typing import Dict, List, Optional

from ..database import execute, execute_many, fetch_all, fetch_one


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def list_flows(user_id: int) -> List[Dict]:
    return await fetch_all(
        "SELECT f.*, (SELECT COUNT(*) FROM flow_nodes n WHERE n.flow_id=f.id) AS node_count "
        "FROM flows f WHERE f.user_id=%s ORDER BY f.updated_at DESC",
        (user_id,),
    )


async def get_flow(flow_id: int, user_id: int) -> Optional[Dict]:
    flow = await fetch_one("SELECT * FROM flows WHERE id=%s AND user_id=%s", (flow_id, user_id))
    if not flow:
        return None
    nodes = await fetch_all(
        "SELECT n.*, c.name AS crew_name FROM flow_nodes n "
        "LEFT JOIN crews c ON c.id=n.crew_id WHERE n.flow_id=%s ORDER BY n.id",
        (flow_id,),
    )
    for node in nodes:
        try:
            node["config"] = json.loads(node.pop("config_json") or "{}")
        except json.JSONDecodeError:
            node["config"] = {}
    edges = await fetch_all(
        "SELECT e.*, s.node_key AS source_key, t.node_key AS target_key "
        "FROM flow_edges e JOIN flow_nodes s ON s.id=e.source_node_id "
        "JOIN flow_nodes t ON t.id=e.target_node_id WHERE e.flow_id=%s "
        "ORDER BY e.priority, e.id",
        (flow_id,),
    )
    flow["nodes"] = nodes
    flow["edges"] = edges
    try:
        flow["state_schema"] = json.loads(flow.pop("state_schema_json") or "{}")
    except json.JSONDecodeError:
        flow["state_schema"] = {}
    return flow


async def _validate_flow(user_id: int, data: Dict) -> None:
    keys = [node.get("node_key") for node in data.get("nodes", [])]
    if not keys:
        raise ValueError("Flow 至少需要一个节点")
    if len(keys) != len(set(keys)) or any(not key for key in keys):
        raise ValueError("Flow 节点 key 不能为空且不能重复")
    crew_ids = {node.get("crew_id") for node in data.get("nodes", []) if node.get("crew_id")}
    if crew_ids:
        placeholders = ",".join(["%s"] * len(crew_ids))
        rows = await fetch_all(
            f"SELECT id FROM crews WHERE user_id=%s AND id IN ({placeholders})",
            (user_id, *crew_ids),
        )
        if {row["id"] for row in rows} != crew_ids:
            raise ValueError("Flow 引用了不存在或无权访问的 Crew")
    key_set = set(keys)
    incoming = {key: 0 for key in keys}
    for edge in data.get("edges", []):
        if edge.get("source_key") not in key_set or edge.get("target_key") not in key_set:
            raise ValueError("Flow 连线引用了不存在的节点")
        if edge.get("source_key") == edge.get("target_key"):
            raise ValueError("Flow 节点不能连接到自身")
        incoming[edge["target_key"]] += 1
    if not any(count == 0 for count in incoming.values()):
        raise ValueError("Flow 必须至少有一个入度为 0 的开始节点")
    for node in data.get("nodes", []):
        if node.get("node_type") == "crew" and not node.get("crew_id"):
            raise ValueError(f"节点“{node.get('name') or node.get('node_key')}”必须选择 Crew")


async def _save_graph(flow_id: int, data: Dict) -> None:
    node_ids: Dict[str, int] = {}
    for node in data.get("nodes", []):
        node_id = await execute(
            "INSERT INTO flow_nodes (flow_id, node_key, name, node_type, crew_id, config_json, "
            "position_x, position_y) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                flow_id,
                node["node_key"],
                node.get("name") or node["node_key"],
                node.get("node_type", "crew"),
                node.get("crew_id"),
                json.dumps(node.get("config", {}), ensure_ascii=False),
                node.get("position_x", 0),
                node.get("position_y", 0),
            ),
        )
        node_ids[node["node_key"]] = node_id
    if data.get("edges"):
        await execute_many(
            "INSERT INTO flow_edges (flow_id, source_node_id, target_node_id, condition_type, "
            "condition_value, priority) VALUES (%s, %s, %s, %s, %s, %s)",
            [
                (
                    flow_id,
                    node_ids[edge["source_key"]],
                    node_ids[edge["target_key"]],
                    edge.get("condition_type", "always"),
                    edge.get("condition_value", ""),
                    edge.get("priority", 0),
                )
                for edge in data["edges"]
            ],
        )


async def create_flow(user_id: int, data: Dict) -> Dict:
    await _validate_flow(user_id, data)
    now = _now()
    flow_id = await execute(
        "INSERT INTO flows (user_id, name, description, state_schema_json, enabled, created_at, "
        "updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            user_id,
            data.get("name") or "新 Flow",
            data.get("description", ""),
            json.dumps(data.get("state_schema", {}), ensure_ascii=False),
            bool(data.get("enabled", True)),
            now,
            now,
        ),
    )
    await _save_graph(flow_id, data)
    return await get_flow(flow_id, user_id)


async def update_flow(flow_id: int, user_id: int, data: Dict) -> Optional[Dict]:
    if not await fetch_one("SELECT id FROM flows WHERE id=%s AND user_id=%s", (flow_id, user_id)):
        return None
    await _validate_flow(user_id, data)
    await execute(
        "UPDATE flows SET name=%s, description=%s, state_schema_json=%s, enabled=%s, "
        "updated_at=%s WHERE id=%s",
        (
            data.get("name") or "新 Flow",
            data.get("description", ""),
            json.dumps(data.get("state_schema", {}), ensure_ascii=False),
            bool(data.get("enabled", True)),
            _now(),
            flow_id,
        ),
    )
    await execute("DELETE FROM flow_nodes WHERE flow_id=%s", (flow_id,))
    await _save_graph(flow_id, data)
    return await get_flow(flow_id, user_id)


async def delete_flow(flow_id: int, user_id: int) -> bool:
    if not await fetch_one("SELECT id FROM flows WHERE id=%s AND user_id=%s", (flow_id, user_id)):
        return False
    await execute("DELETE FROM chat_sessions WHERE target_type='flow' AND target_id=%s AND user_id=%s", (flow_id, user_id))
    await execute("DELETE FROM flows WHERE id=%s AND user_id=%s", (flow_id, user_id))
    return True
