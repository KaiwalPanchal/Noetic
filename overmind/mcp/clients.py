"""MCP client config generator: wires `overmind-mcp` into Claude Desktop, Claude Code, Cursor and Windsurf.

Each client keeps its servers in a JSON file under "mcpServers". We merge a single "overmind" entry
into that file and leave every other key alone. A malformed existing file is never overwritten.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import sys

SERVER_KEY = "overmind"
CLIENTS = ("claude-desktop", "claude-code", "cursor", "windsurf")


@dataclass
class ClientResult:
  client: str
  path: Path
  action: str  # created | updated | unchanged | dry-run | error
  detail: str = ""


def server_entry(vault: Path) -> dict:
  """How a client launches the server: the installed script if present, else `uvx` (no install needed)."""
  exe = shutil.which("overmind-mcp")
  if exe:
    command, args = exe, []
  else:
    command, args = "uvx", ["--from", "overmind-engine", "overmind-mcp"]
  return {"command": command, "args": [*args, "--vault", str(vault)]}


def config_path(client: str, vault: Path, scope: str = "project", home: Path | None = None) -> Path:
  """Where `client` reads its MCP servers from. `scope` ("project" | "global") only matters for Cursor."""
  home = home or Path.home()
  if client == "claude-desktop":
    if sys.platform == "win32":
      base = Path(os.environ.get("APPDATA") or home / "AppData" / "Roaming")
    elif sys.platform == "darwin":
      base = home / "Library" / "Application Support"
    else:
      base = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    return base / "Claude" / "claude_desktop_config.json"
  if client == "claude-code":
    return vault / ".mcp.json"
  if client == "cursor":
    return (home / ".cursor" / "mcp.json") if scope == "global" else (vault / ".cursor" / "mcp.json")
  if client == "windsurf":
    return home / ".codeium" / "windsurf" / "mcp_config.json"
  raise ValueError(f"unknown client '{client}' (known: {', '.join(CLIENTS)})")


def write_client(client: str, vault: Path, scope: str = "project", dry_run: bool = False,
                 home: Path | None = None) -> ClientResult:
  path = config_path(client, vault, scope, home)
  entry = server_entry(vault)
  data: dict = {}
  existed = path.exists()
  if existed:
    try:
      data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError as e:
      return ClientResult(client, path, "error", f"existing file is not valid JSON ({e}); left untouched")
    if not isinstance(data, dict) or not isinstance(data.get("mcpServers", {}), dict):
      return ClientResult(client, path, "error", "existing file has an unexpected shape; left untouched")
  servers = data.setdefault("mcpServers", {})
  if servers.get(SERVER_KEY) == entry:
    return ClientResult(client, path, "unchanged")
  servers[SERVER_KEY] = entry
  if dry_run:
    return ClientResult(client, path, "dry-run", json.dumps({SERVER_KEY: entry}))
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
  return ClientResult(client, path, "updated" if existed else "created")
