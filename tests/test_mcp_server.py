"""Tests for the native Model Context Protocol (MCP) server."""

from pathlib import Path
import pytest

from noetic.mcp.server import create_mcp_server


def test_mcp_server_initialization():
  server = create_mcp_server()
  assert server.name == "Noetic"
  assert server.version == "0.2.0"
  assert "autonomous agent harness" in server.description.lower()


def test_mcp_tool_inspect_code_safety_safe():
  server = create_mcp_server()
  # Find tool by name
  tools = {t.name: t for t in server._tool_manager.list_tools()}
  assert "inspect_code_safety" in tools

  inspect_tool = tools["inspect_code_safety"]
  res = inspect_tool.fn(code="x = 1 + 2\nprint(x)")
  assert res["safe"] is True
  assert res["violations"] == []


def test_mcp_tool_inspect_code_safety_unsafe():
  server = create_mcp_server()
  tools = {t.name: t for t in server._tool_manager.list_tools()}
  inspect_tool = tools["inspect_code_safety"]

  res = inspect_tool.fn(code="import os\nos.system('calc.exe')")
  assert res["safe"] is False
  assert len(res["violations"]) > 0


def test_mcp_tool_validate_thread_security_violation(tmp_path: Path):
  server = create_mcp_server(vault_override=tmp_path)
  tools = {t.name: t for t in server._tool_manager.list_tools()}
  validate_tool = tools["validate_thread"]

  res = validate_tool.fn(file_path="../outside.md")
  assert res["ok"] is False
  assert "Security violation" in res["error"]


def test_mcp_tool_check_json_schema_missing():
  server = create_mcp_server()
  tools = {t.name: t for t in server._tool_manager.list_tools()}
  check_tool = tools["check_json_schema"]

  res = check_tool.fn(data={"key": "val"}, schema_name="nonexistent_schema_xyz")
  assert res["ok"] is False
  assert "not found" in res["error"].lower()


def test_mcp_resource_stances():
  server = create_mcp_server()
  resources = {r.uri: r for r in server._resource_manager.list_resources()}
  assert "noetic://stances" in resources
  assert "noetic://status" in resources
  assert "noetic://frameworks" in resources


def _server_for(vault):
  return create_mcp_server(vault_override=vault)


def test_mcp_registry_resources_registered():
  uris = {str(r.uri) for r in create_mcp_server()._resource_manager.list_resources()}
  assert {"noetic://projects", "noetic://quests", "noetic://briefing"} <= uris


def test_mcp_list_projects_and_get_briefing_tools(ovault):
  import json
  tools = {t.name: t for t in _server_for(ovault)._tool_manager.list_tools()}
  assert "list_projects" in tools and "get_briefing" in tools
  projects = tools["list_projects"].fn()
  assert {p["name"] for p in projects["projects"]} == {"Alpha", "Beta", "Gamma", "Delta"}
  b = tools["get_briefing"].fn()
  assert b["focus"]["name"] == "QUEST-001"
  assert "SECRET-PROFILE-TOKEN" not in json.dumps(projects) + json.dumps(b)


def test_mcp_registry_resources_return_json_and_hide_profile(ovault):
  import json
  res = {str(r.uri): r for r in _server_for(ovault)._resource_manager.list_resources()}
  for uri in ("noetic://projects", "noetic://quests", "noetic://briefing"):
    text = res[uri].fn()
    assert "SECRET-PROFILE-TOKEN" not in text
    json.loads(text)


def test_mcp_registry_without_vault_is_graceful(tmp_path):
  tools = {t.name: t for t in _server_for(tmp_path)._tool_manager.list_tools()}
  assert tools["list_projects"].fn()["projects"] == []


def test_mcp_stdio_handshake(tmp_path):
  """Spawn the real server over stdio and list its tools through the MCP client."""
  import asyncio
  import sys

  from mcp import ClientSession, StdioServerParameters
  from mcp.client.stdio import stdio_client

  async def go():
    params = StdioServerParameters(command=sys.executable, args=["-m", "noetic.mcp.server", "--vault", str(tmp_path)])
    async with stdio_client(params) as (read, write):
      async with ClientSession(read, write) as session:
        await session.initialize()
        return {t.name for t in (await session.list_tools()).tools}

  names = asyncio.run(asyncio.wait_for(go(), timeout=60))
  assert {"get_briefing", "list_projects", "inspect_code_safety", "validate_thread"} <= names
