"""Tests for the native Model Context Protocol (MCP) server."""

from pathlib import Path
import pytest

from taste_engine.mcp.server import create_mcp_server


def test_mcp_server_initialization():
  server = create_mcp_server()
  assert server.name == "OverMind Taste Engine"
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
  assert "overmind://stances" in resources
  assert "overmind://status" in resources
  assert "overmind://frameworks" in resources
