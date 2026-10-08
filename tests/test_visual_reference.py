"""docs/VISUAL_REFERENCE.md must name every CLI command, MCP tool/resource, pipeline and slash command."""

from pathlib import Path

from typer.main import get_command

from overmind.cli import app
from overmind.mcp.server import create_mcp_server
from overmind.orchestration.loader import resource_dirs
from overmind.orchestration.registry import discover

DOC = (Path(__file__).resolve().parents[1] / "docs" / "VISUAL_REFERENCE.md").read_text(encoding="utf-8")


def test_every_cli_command_is_documented():
  missing = [n for n in get_command(app).commands if n not in DOC]
  assert not missing, f"add to VISUAL_REFERENCE.md: {missing}"


def test_every_pipeline_is_documented():
  missing = [n for n in discover() if n not in DOC]
  assert not missing, f"add to VISUAL_REFERENCE.md: {missing}"


def test_every_slash_command_is_documented():
  names = {p.stem for d in resource_dirs("commands") for p in d.glob("*.md")}
  missing = [n for n in names if f"/{n}" not in DOC]
  assert not missing, f"add to VISUAL_REFERENCE.md: {missing}"


def test_every_mcp_tool_and_resource_is_documented():
  server = create_mcp_server()
  tools = [t.name for t in server._tool_manager.list_tools()] if hasattr(server, "_tool_manager") else []
  assert tools, "could not enumerate MCP tools"
  missing = [t for t in tools if t not in DOC]
  assert not missing, f"add to VISUAL_REFERENCE.md: {missing}"
