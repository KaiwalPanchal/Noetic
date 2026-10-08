"""MCP client config generator: merge, don't clobber."""

import json
from pathlib import Path

from overmind.mcp.clients import CLIENTS, SERVER_KEY, config_path, write_client


def test_creates_config_with_overmind_entry(tmp_path: Path):
  vault = tmp_path / "v"
  vault.mkdir()
  r = write_client("cursor", vault, home=tmp_path / "home")
  assert r.action == "created" and r.path == vault / ".cursor" / "mcp.json"
  entry = json.loads(r.path.read_text(encoding="utf-8"))["mcpServers"][SERVER_KEY]
  assert entry["args"][-2:] == ["--vault", str(vault)]


def test_merges_without_touching_other_servers_and_is_idempotent(tmp_path: Path):
  vault = tmp_path / "v"
  vault.mkdir()
  path = vault / ".mcp.json"
  path.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}, "theme": "dark"}), encoding="utf-8")
  assert write_client("claude-code", vault).action == "updated"
  data = json.loads(path.read_text(encoding="utf-8"))
  assert data["mcpServers"]["other"] == {"command": "x"} and data["theme"] == "dark" and SERVER_KEY in data["mcpServers"]
  assert write_client("claude-code", vault).action == "unchanged"


def test_malformed_file_is_left_alone(tmp_path: Path):
  vault = tmp_path / "v"
  vault.mkdir()
  (vault / ".mcp.json").write_text("{not json", encoding="utf-8")
  r = write_client("claude-code", vault)
  assert r.action == "error" and (vault / ".mcp.json").read_text(encoding="utf-8") == "{not json"


def test_dry_run_writes_nothing_and_all_clients_have_paths(tmp_path: Path):
  vault = tmp_path / "v"
  vault.mkdir()
  assert write_client("windsurf", vault, dry_run=True, home=tmp_path / "h").action == "dry-run"
  assert not (tmp_path / "h").exists()
  for c in CLIENTS:
    assert config_path(c, vault, home=tmp_path / "h").name.endswith(".json")
