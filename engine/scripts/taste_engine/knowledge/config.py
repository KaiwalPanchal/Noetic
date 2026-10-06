"""Knowledge layer: vault config. Where everything lives and how the engine is wired.

Finds the vault by locating `taste-engine.config.json`, checked in this order:
1. the TASTE_ENGINE_VAULT environment variable
2. the current directory and its parents
3. this script's directory and its parents
"""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import re

CONFIG_NAME = "taste-engine.config.json"

# <engine>/scripts/taste_engine/knowledge/config.py → <engine>
ENGINE_DIR = Path(__file__).resolve().parents[3]
PROMPTS_DIR = ENGINE_DIR / "prompts"
SCHEMAS_DIR = ENGINE_DIR / "schemas"

DEFAULTS = {
  "owner": "Owner",
  "agent": "Claude Code",
  "x_char_limit": 280,
  "paths": {
    "engine": "taste-engine",
    "frameworks": "frameworks",
    "twitter": "Twitter",
    "overmind": None,
  },
  # Which agent CLI runs each pipeline step. Override per run with --agent.
  "agents": {
    "ingest": "claude",
    "curate": "claude",
    "research": "agy",
    "draft": "claude",
    "journey": "claude",
    "deconstruct": "claude",
    "build": "codex",
    "fallback": ["claude", "agy", "codex"],
  },
  # Optional per-agent model, e.g. {"claude": "opus", "codex": "gpt-5"}.
  "models": {"claude": "sonnet"},
  # Vault folders the pipeline never reads for context (curate/research/journey).
  "private_paths": [],
}


class Config:
  def __init__(self, vault: Path, data: dict):
    self.vault = vault
    self.owner: str = data.get("owner", DEFAULTS["owner"])
    self.agent: str = data.get("agent", DEFAULTS["agent"])
    self.x_char_limit: int = int(data.get("x_char_limit", DEFAULTS["x_char_limit"]))
    paths = {**DEFAULTS["paths"], **data.get("paths", {})}
    self.engine = vault / paths["engine"]
    self.frameworks = vault / paths["frameworks"]
    self.twitter = vault / paths["twitter"]
    self.overmind = vault / paths["overmind"] if paths.get("overmind") else None
    self.agents: dict = {**DEFAULTS["agents"], **data.get("agents", {})}
    self.models: dict = {**DEFAULTS["models"], **data.get("models", {})}
    self.private_paths: list[str] = data.get("private_paths", DEFAULTS["private_paths"])
    self.state_dir = vault / ".taste-engine"


def _search_up(start: Path) -> Path | None:
  for folder in [start, *start.parents]:
    if (folder / CONFIG_NAME).is_file():
      return folder
  return None


def find_vault() -> Path:
  env = os.environ.get("TASTE_ENGINE_VAULT")
  if env and (Path(env) / CONFIG_NAME).is_file():
    return Path(env)
  for start in (Path.cwd(), Path(__file__).resolve().parent):
    found = _search_up(start)
    if found:
      return found
  raise SystemExit(
    f"Could not find {CONFIG_NAME}. Run install.py --vault <path> first, "
    "or set TASTE_ENGINE_VAULT."
  )


def load_config() -> Config:
  vault = find_vault()
  data = json.loads((vault / CONFIG_NAME).read_text(encoding="utf-8"))
  return Config(vault, data)


def slugify(text: str) -> str:
  text = text.lower().strip()
  text = re.sub(r"[^\w\s-]", "", text)
  return re.sub(r"[\s_-]+", "-", text).strip("-")


def today() -> str:
  return datetime.now().strftime("%Y-%m-%d")


def frontmatter(cfg: Config, author: str = "ai-agent", extra: dict | None = None) -> str:
  """AI-authored notes carry an attribution callout; human notes stay clean."""
  lines = ["---", f"author: {author}"]
  if author == "ai-agent":
    lines.append(f"agent: {cfg.agent}")
  lines.append(f"created: {today()}")
  lines.append(f"status: {'draft-for-review' if author == 'ai-agent' else 'curated'}")
  for key, value in (extra or {}).items():
    lines.append(f"{key}: {value}")
  lines.append("---")
  if author == "ai-agent":
    lines.append(
      f"> [!NOTE] Authored by AI Agent ({cfg.agent}) · Pending {cfg.owner}'s review and personal curation."
    )
  return "\n".join(lines) + "\n\n"
