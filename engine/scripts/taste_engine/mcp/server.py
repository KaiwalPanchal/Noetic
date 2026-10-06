"""Model Context Protocol (MCP) Native Server for OverMind.

Complies with MCP 2.x specification exposing knowledge base resources and
operational tools over stdio, SSE, or streamable-http.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from mcp.server.mcpserver import MCPServer
from taste_engine.knowledge.config import find_vault, load_config
from taste_engine.security.policy_gate import (
    SecurityViolation,
    validate_python_ast,
    validate_vault_path,
)


def create_mcp_server(vault_override: Path | None = None) -> MCPServer:
  """Instantiates and configures the OverMind MCP Server."""
  server = MCPServer(
      name="OverMind Taste Engine",
      version="0.2.0",
      description="Autonomous agent harness and taste engine for personal knowledge vaults",
  )

  def _get_cfg():
    if vault_override:
      from taste_engine.knowledge.config import Config, CONFIG_NAME

      cfg_file = vault_override / CONFIG_NAME
      data = json.loads(cfg_file.read_text(encoding="utf-8")) if cfg_file.exists() else {}
      return Config(vault_override, data)
    try:
      return load_config()
    except (Exception, SystemExit):
      return None

  # ── Resources ─────────────────────────────────────────────────────────────

  @server.resource("overmind://stances")
  def resource_stances() -> str:
    """Returns active taste stances and negative filters guiding project decisions."""
    cfg = _get_cfg()
    if not cfg:
      return "Vault configuration not loaded."
    interests = cfg.engine / "interests.md"
    if interests.exists():
      return interests.read_text(encoding="utf-8")
    stances_dir = cfg.engine / "01-taste-graph" / "stances"
    if stances_dir.exists():
      files = sorted(stances_dir.glob("*.md"))
      if files:
        return "\n\n---\n\n".join(f.read_text(encoding="utf-8") for f in files)
    return "No active stances found in vault."

  @server.resource("overmind://status")
  def resource_status() -> str:
    """Returns the current operating status and recent run activity."""
    cfg = _get_cfg()
    if not cfg:
      return json.dumps({"status": "no_vault", "active": False})
    runs_dir = cfg.state_dir / "runs"
    runs = sorted(runs_dir.glob("*.json"), reverse=True)[:5] if runs_dir.exists() else []
    recent = []
    for f in runs:
      try:
        data = json.loads(f.read_text(encoding="utf-8"))
        recent.append({"id": data.get("id"), "status": data.get("status"), "command": data.get("command")})
      except Exception:
        continue
    return json.dumps({"owner": cfg.owner, "agent": cfg.agent, "recent_runs": recent}, indent=2)

  @server.resource("overmind://frameworks")
  def resource_frameworks() -> str:
    """Lists available thinking frameworks and mental models in the vault."""
    cfg = _get_cfg()
    if not cfg:
      return "[]"
    frameworks_dir = cfg.frameworks
    names = []
    if frameworks_dir.exists():
      for f in frameworks_dir.glob("*.md"):
        names.append(f.stem)
    return json.dumps(names, indent=2)

  # ── Tools ─────────────────────────────────────────────────────────────────

  @server.tool()
  def validate_thread(file_path: str, limit: int = 280) -> dict:
    """Validates a Twitter/X thread draft file against character limits and URL weighting."""
    cfg = _get_cfg()
    if not cfg:
      return {"ok": False, "error": "Vault configuration not found."}

    try:
      safe_file = validate_vault_path(file_path, cfg.vault)
    except SecurityViolation as e:
      return {"ok": False, "error": f"Security violation: {e}"}

    if not safe_file.exists():
      return {"ok": False, "error": f"File not found: {file_path}"}

    from taste_engine.tools.tweets import weighted_length
    content = safe_file.read_text(encoding="utf-8")
    import re
    chunks = re.split(r"(?=###\s+Tweet\s+\d+)", content)
    tweets = []
    all_passed = True

    for chunk in chunks:
      chunk = chunk.strip()
      if not chunk or not chunk.startswith("###"):
        continue
      lines = chunk.splitlines()
      header = lines[0].strip()
      body = "\n".join(lines[1:]).strip()
      body = re.split(r"\n---\s*(\n|$)", body)[0].strip()
      count = weighted_length(body)
      ok = count <= limit and bool(body)
      all_passed &= ok
      tweets.append({"header": header, "length": count, "limit": limit, "passed": ok})

    return {"ok": True, "all_passed": all_passed, "total_tweets": len(tweets), "tweets": tweets}

  @server.tool()
  def inspect_code_safety(code: str) -> dict:
    """Performs pre-execution AST static analysis on Python code to verify execution safety."""
    try:
      validate_python_ast(code)
      return {"safe": True, "violations": []}
    except SecurityViolation as e:
      return {"safe": False, "violations": [str(e)]}

  @server.tool()
  def check_json_schema(data: dict, schema_name: str) -> dict:
    """Validates arbitrary structured output against an OverMind JSON schema."""
    from taste_engine.knowledge.config import SCHEMAS_DIR
    schema_file = SCHEMAS_DIR / f"{schema_name}.json"
    if not schema_file.exists():
      # check projects
      cfg = _get_cfg()
      if cfg:
        twitter_schema = cfg.vault / "taste-engine" / "projects" / "twitter" / "schemas" / f"{schema_name}.json"
        if twitter_schema.exists():
          schema_file = twitter_schema

    if not schema_file.exists():
      return {"ok": False, "error": f"Schema '{schema_name}' not found."}

    import jsonschema
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    try:
      jsonschema.validate(instance=data, schema=schema)
      return {"ok": True, "valid": True, "errors": []}
    except jsonschema.ValidationError as err:
      return {"ok": True, "valid": False, "errors": [err.message]}

  @server.tool()
  def get_active_stances() -> dict:
    """Returns structured list of user's core stances and negative filters."""
    cfg = _get_cfg()
    if not cfg:
      return {"error": "Vault not loaded"}
    interests_file = cfg.engine / "interests.md"
    content = interests_file.read_text(encoding="utf-8") if interests_file.exists() else ""
    return {"owner": cfg.owner, "content": content}

  return server


def main():
  """Console entry point for `overmind-mcp`."""
  parser = argparse.ArgumentParser(description="OverMind Model Context Protocol (MCP) Server")
  parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio",
                      help="MCP transport protocol (default: stdio)")
  parser.add_argument("--vault", type=str, default=None, help="Path to markdown vault directory")
  parser.add_argument("--port", type=int, default=8000, help="Port for SSE/HTTP transport (default: 8000)")
  args = parser.parse_args()

  vault_dir = Path(args.vault).resolve() if args.vault else None
  server = create_mcp_server(vault_dir)

  if args.transport == "stdio":
    server.run(transport="stdio")
  elif args.transport == "sse":
    server.run(transport="sse", port=args.port)
  else:
    server.run(transport="streamable-http", port=args.port)


if __name__ == "__main__":
  main()
