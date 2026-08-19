"""Skill Action tools declared by skill.json manifests."""
import json
import logging
import re
from ipaddress import ip_address
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from urllib.parse import quote

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model

from ..config import SKILL_ACTION_ALLOW_PRIVATE_NETWORK
from ..services.skill_service import read_skill_action_manifest

log = logging.getLogger("agent-platform")

_TOOL_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def _is_private_host(hostname: str) -> bool:
    if not hostname:
        return True
    if hostname.lower() in _LOCAL_HOSTS:
        return True
    try:
        addr = ip_address(hostname)
    except ValueError:
        return False
    return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved


def _validate_action_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False
    if not SKILL_ACTION_ALLOW_PRIVATE_NETWORK and _is_private_host(parsed.hostname or ""):
        return False
    return True


def _python_type(schema: Dict) -> type:
    value_type = schema.get("type", "string")
    if value_type == "integer":
        return int
    if value_type == "number":
        return float
    if value_type == "boolean":
        return bool
    if value_type == "array":
        return list
    if value_type == "object":
        return dict
    return str


def _create_args_schema(parameters: Dict) -> type:
    fields = {}
    for name, spec in parameters.items():
        if not isinstance(spec, dict):
            spec = {"type": "string", "description": ""}
        description = spec.get("description", "")
        py_type = _python_type(spec)
        if spec.get("required") is True:
            fields[name] = (py_type, Field(description=description))
        else:
            fields[name] = (Optional[py_type], Field(default=None, description=description))
    if not fields:
        return BaseModel
    return create_model("SkillActionInput", **fields)


def _render_url(url: str, arguments: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    remaining = dict(arguments)
    for key, value in list(arguments.items()):
        token = "{" + key + "}"
        if token in url:
            url = url.replace(token, quote(str(value), safe=""))
            remaining.pop(key, None)
    return url, remaining


async def _call_http_action(action: Dict, arguments: Dict[str, Any]) -> str:
    method = action["method"]
    url, remaining_args = _render_url(action["url"], arguments)
    headers = action.get("headers") or {}
    timeout = float(action.get("timeout", 30))

    request_kwargs = {"headers": headers}
    if method == "GET":
        request_kwargs["params"] = remaining_args
    else:
        request_kwargs["json"] = remaining_args

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(method, url, **request_kwargs)
        response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            return json.dumps(response.json(), ensure_ascii=False)
        except ValueError:
            pass
    return response.text


def _normalize_action(raw_action: Dict, skill: Dict) -> Optional[Dict]:
    if not isinstance(raw_action, dict):
        return None
    if raw_action.get("type", "http") != "http":
        return None

    name = str(raw_action.get("name", "")).strip()
    if not _TOOL_NAME_RE.match(name):
        log.warning("[SkillAction] skill=%s 跳过非法工具名: %s", skill.get("name"), name)
        return None

    method = str(raw_action.get("method", "GET")).upper()
    url = str(raw_action.get("url", "")).strip()
    if method not in _HTTP_METHODS or not _validate_action_url(url):
        log.warning("[SkillAction] skill=%s tool=%s HTTP 配置无效", skill.get("name"), name)
        return None

    parameters = raw_action.get("parameters") or {}
    if not isinstance(parameters, dict):
        parameters = {}

    headers = raw_action.get("headers") or {}
    if not isinstance(headers, dict):
        headers = {}

    return {
        "name": name,
        "description": str(raw_action.get("description") or f"HTTP action from Skill {skill.get('name', '')}"),
        "method": method,
        "url": url,
        "headers": {str(k): str(v) for k, v in headers.items()},
        "parameters": parameters,
        "timeout": raw_action.get("timeout", 30),
    }


def build_skill_action_tools(skills: List[Dict]) -> List[StructuredTool]:
    """Build LangChain tools from optional skill.json manifests."""
    tools = []
    used_names = set()

    for skill in skills:
        try:
            manifest = read_skill_action_manifest(skill["id"])
        except ValueError as exc:
            log.warning("[SkillAction] skill=%s manifest 无效: %s", skill.get("name"), exc)
            continue

        raw_tools = manifest.get("tools", [])
        if not isinstance(raw_tools, list):
            continue

        for raw_action in raw_tools:
            action = _normalize_action(raw_action, skill)
            if not action:
                continue
            if action["name"] in used_names:
                log.warning("[SkillAction] 跳过重复工具名: %s", action["name"])
                continue
            used_names.add(action["name"])

            args_schema = _create_args_schema(action["parameters"])

            def make_executor(current_action):
                async def executor(**kwargs):
                    return await _call_http_action(current_action, kwargs)
                return executor

            tools.append(
                StructuredTool.from_function(
                    coroutine=make_executor(action),
                    name=action["name"],
                    description=action["description"],
                    args_schema=args_schema,
                )
            )

    if tools:
        log.info("[SkillAction] loaded %d HTTP action tools", len(tools))
    return tools
