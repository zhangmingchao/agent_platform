"""技能相关的 LangChain 工具定义。"""
import json
import logging
from typing import Dict, List

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from ..services.skill_service import read_skill_entrypoint, read_skill_file
from .skill_actions import build_skill_action_tools

log = logging.getLogger(__name__)


class SkillInput(BaseModel):
    command: str = Field(description="要执行的技能名称")


class SkillFileInput(BaseModel):
    skill_name: str = Field(description="所属的技能名称")
    path: str = Field(description="技能包内的相对路径")


def build_skill_tools(skills: List[Dict], plugin_ids: List[str] | None = None) -> List[StructuredTool]:
    """构建统一技能入口；skills 为数据库技能，plugin_ids 为当前 Agent 绑定的插件。"""
    from ..plugins.registry import get_manifest, read_plugin_skill

    plugins_map = {get_manifest(pid).skill_name: pid for pid in (plugin_ids or []) if get_manifest(pid).skill_name}
    # 绑定插件的同名技能优先，确保说明和工具版本一致，同时避免重复 Skill 工具。
    skills = [skill for skill in skills if skill["name"] not in plugins_map]
    if not skills and not plugins_map:
        return []

    skills_map = {s["name"]: s for s in skills}

    available = []
    for s in skills:
        available.append(
            f'<skill>\n  <name>{s["name"]}</name>\n  <description>{s["description"]}</description>\n</skill>'
        )
    for name, plugin_id in plugins_map.items():
        available.append(f'<skill>\n  <name>{name}</name>\n  <description>{get_manifest(plugin_id).description}</description>\n</skill>')
    skills_xml = "\n".join(available)

    skill_description = f"""Execute a skill within the main conversation.
<available_skills>
{skills_xml}
</available_skills>

Invoke a skill by its name to get full instructions and context for the task."""

    def execute_skill(command: str) -> str:
        if command in plugins_map:
            return read_plugin_skill(plugins_map[command]).content
        skill = skills_map.get(command)
        if not skill:
            return f"Unknown skill: {command}"
        content = read_skill_entrypoint(skill["id"], skill.get("content", ""))
        log.info(f"[Skill] name={command} | len={len(content)}")
        return content

    def execute_skill_file(skill_name: str, path: str) -> str:
        if skill_name in plugins_map:
            try:
                return read_plugin_skill(plugins_map[skill_name], path).content
            except ValueError as exc:
                return json.dumps({"error": str(exc)}, ensure_ascii=False)
        skill = skills_map.get(skill_name)
        if not skill:
            return f"Unknown skill: {skill_name}"
        try:
            content = read_skill_file(skill["id"], path)
            log.info(f"[SkillFile] name={skill_name} | path={path} | len={len(content)}")
            return content
        except ValueError as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)

    skill_tool = StructuredTool.from_function(
        func=execute_skill,
        name="Skill",
        description=skill_description,
        args_schema=SkillInput,
    )

    file_tool = StructuredTool.from_function(
        func=execute_skill_file,
        name="SkillFile",
        description="Read a UTF-8 text file referenced by a Skill, such as references/guide.md. Call Skill first, then read only files it references.",
        args_schema=SkillFileInput,
    )

    return [skill_tool, file_tool, *build_skill_action_tools(skills)]
