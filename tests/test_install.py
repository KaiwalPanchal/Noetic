"""install.py smoke test: the twitter pack is installed from its canonical package location."""

import json
from pathlib import Path
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parent.parent


def test_install_into_fresh_vault_includes_twitter_pack(tmp_path: Path):
  vault = tmp_path / "vault"
  vault.mkdir()
  res = subprocess.run([sys.executable, str(REPO / "install.py"), "--vault", str(vault)],
                       capture_output=True, text=True, encoding="utf-8")
  assert res.returncode == 0, res.stderr
  assert (vault / ".claude" / "commands" / "draft.md").is_file()           # pack command
  engine = vault / "taste-engine" / "scripts"
  assert (engine / "workflows" / "twitter" / "pipelines" / "draft.py").is_file()   # pack pipeline
  assert (engine / "workflows" / "twitter" / "scripts" / "thread_validator.py").is_file()  # pack script
  assert (engine / "noetic" / "__init__.py").is_file()                    # core package
  assert (vault / "Twitter" / "journey").is_dir()


def run_install(vault: Path, *extra: str):
  return subprocess.run([sys.executable, str(REPO / "install.py"), "--vault", str(vault), *extra],
                        capture_output=True, text=True, encoding="utf-8")


def test_install_defaults_to_all_adapters_and_records_choice(tmp_path: Path):
  vault = tmp_path / "v"
  vault.mkdir()
  res = run_install(vault)
  assert res.returncode == 0, res.stderr
  cfg = json.loads((vault / "taste-engine.config.json").read_text(encoding="utf-8"))
  assert cfg["adapters"] == ["claude", "codex", "gemini", "antigravity"]
  for f in ["CLAUDE.md", "AGENTS.md", "GEMINI.md", ".gemini/commands/apply.toml",
            ".agent/skills/overmind-apply/SKILL.md", "taste-engine/canonical/commands/apply.md",
            "taste-engine/canonical/AGENTS.block.md"]:
    assert (vault / f).is_file(), f
  assert not (vault / "OverMind").exists()  # wiki is opt-in


def test_install_agents_flag_limits_output_and_is_remembered(tmp_path: Path):
  vault = tmp_path / "v"
  vault.mkdir()
  assert run_install(vault, "--agents", "gemini").returncode == 0
  assert (vault / "GEMINI.md").is_file() and not (vault / "CLAUDE.md").exists()
  assert not (vault / ".claude").exists()
  assert run_install(vault).returncode == 0  # re-run keeps the recorded choice
  assert not (vault / "CLAUDE.md").exists()
  assert json.loads((vault / "taste-engine.config.json").read_text(encoding="utf-8"))["adapters"] == ["gemini"]
  assert run_install(vault, "--agents", "bogus").returncode != 0


def test_install_is_idempotent_and_preserves_user_text(tmp_path: Path):
  vault = tmp_path / "v"
  vault.mkdir()
  (vault / "CLAUDE.md").write_text("# Mine\n\nprivate rules\n", encoding="utf-8")
  assert run_install(vault).returncode == 0
  snap = {p: p.read_bytes() for p in vault.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
  assert run_install(vault).returncode == 0
  assert snap == {p: p.read_bytes() for p in vault.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
  assert "private rules" in (vault / "CLAUDE.md").read_text(encoding="utf-8")


def test_with_wiki_copies_template_and_never_overwrites(tmp_path: Path):
  vault = tmp_path / "v"
  (vault / "OverMind").mkdir(parents=True)
  (vault / "OverMind" / "OVERMIND.md").write_text("my constitution\n", encoding="utf-8")
  res = run_install(vault, "--with-wiki")
  assert res.returncode == 0, res.stderr
  wiki = vault / "OverMind"
  assert (wiki / "OVERMIND.md").read_text(encoding="utf-8") == "my constitution\n"
  for f in ["wiki/projects/_template.md", "wiki/quests/XP-LEDGER.md", "wiki/profile/README.md", "README.md"]:
    assert (wiki / f).is_file(), f
  for d in ["profile", "competencies", "goals", "projects", "quests", "log"]:
    assert (wiki / "wiki" / d).is_dir()
  tpl = (wiki / "wiki/projects/_template.md").read_text(encoding="utf-8")
  for key in ["name:", "status:", "goal:", "competency:", "repo:", "next_action:", "last_touched:", "gate:"]:
    assert key in tpl
  assert "private by design" in (wiki / "README.md").read_text(encoding="utf-8")
  agents_md = (vault / "AGENTS.md").read_text(encoding="utf-8")
  assert "OverMind/OVERMIND.md" in agents_md  # constitution is wired into the generated block


def test_wiki_seed_is_personless():
  text = "\n".join(p.read_text(encoding="utf-8") for p in (REPO / "noetic" / "seed" / "overmind-wiki").rglob("*") if p.is_file())
  assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
  from tests.conftest import private_terms
  assert not [t for t in private_terms() if t in text.lower()] and "C:\\" not in text


def test_seed_block_is_provider_neutral_and_old_claude_block_is_gone():
  assert (REPO / "noetic" / "seed" / "AGENTS.block.md").is_file()
  assert not (REPO / "noetic" / "seed" / "CLAUDE.block.md").exists()


def test_cli_install_and_mcp_config(tmp_path: Path):
  from typer.testing import CliRunner

  from noetic.cli import app

  vault = tmp_path / "v"
  vault.mkdir()
  runner = CliRunner()
  res = runner.invoke(app, ["install", "--vault", str(vault), "--agents", "claude"])
  assert res.exit_code == 0, res.output
  assert (vault / "CLAUDE.md").is_file() and (vault / "taste-engine.config.json").is_file()
  res = runner.invoke(app, ["mcp-config", "--vault", str(vault), "--client", "claude-code"])
  assert res.exit_code == 0, res.output
  assert "noetic" in json.loads((vault / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
  assert runner.invoke(app, ["mcp-config", "--vault", str(vault), "--client", "bogus"]).exit_code == 2


def test_launchers_exist_and_call_the_cli():
  assert "noetic" in (REPO / "install.sh").read_text(encoding="utf-8") and "uvx" in (REPO / "install.sh").read_text(encoding="utf-8")
  ps = (REPO / "install.ps1").read_text(encoding="utf-8")
  assert "uvx" in ps and "'install'" in ps
