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

# .../overmind/knowledge/config.py → the overmind package; agent contracts live beside the runners.
PACKAGE_DIR = Path(__file__).resolve().parents[1]
AGENTS_DIR = PACKAGE_DIR / "agents"

DEFAULTS = {
  "owner": "Owner",
  "agent": "AI agent",  # display name written into note frontmatter
  "paths": {
    "engine": "taste-engine",
    "frameworks": "frameworks",
    "overmind": None,
  },
  # Which agent CLIs run pipeline steps, in preference order. No default is
  # hardcoded: leave empty and the first installed adapter is used.
  #   "agents": ["a", "b"]                 ordered list (first = preferred, rest = fallback)
  #   "steps":  {"curate": "b"}            per-step override (a name or an ordered list)
  #   "commands": {"mycli": {"argv": ["mycli", "--prompt-file", "{prompt_file}"]}}   generic CLIs
  # The legacy {"agents": {"curate": "x", "fallback": [...]}} mapping is still read.
  "agents": [],
  "steps": {},
  "commands": {},
  # Optional per-agent model, e.g. {"some-agent": "model-name"}.
  "models": {},
  # Vault folders the pipeline never reads for context (curate/research/journey).
  "private_paths": [],
  "projects": {},
  # Optional persona file (vault-relative) that sets the orchestrator's tone. Absent by default.
  "persona": None,
}


class Config:
  def __init__(self, vault: Path, data: dict):
    self.vault = vault
    self.owner: str = data.get("owner", DEFAULTS["owner"])
    self.agent: str = data.get("agent", DEFAULTS["agent"])
    paths = {**DEFAULTS["paths"], **data.get("paths", {})}
    self.engine = vault / paths["engine"]
    self.frameworks = vault / paths["frameworks"]
    self.overmind = vault / paths["overmind"] if paths.get("overmind") else None
    # Backward compatible optional project paths
    self.twitter = vault / paths["twitter"] if paths.get("twitter") else vault / "Twitter"
    self.x_char_limit: int = int(data.get("x_char_limit", 280))
    self.projects: dict = data.get("projects", {})
    raw_agents = data.get("agents", DEFAULTS["agents"])
    self.agent_list: list[str] = list(raw_agents) if isinstance(raw_agents, (list, tuple)) else _legacy_list(raw_agents)
    self.agents: dict = dict(raw_agents) if isinstance(raw_agents, dict) else {}  # legacy per-step mapping
    self.steps: dict = {**DEFAULTS["steps"], **data.get("steps", {})}
    self.commands: dict = {**DEFAULTS["commands"], **data.get("commands", {})}
    self.models: dict = {**DEFAULTS["models"], **data.get("models", {})}
    persona = data.get("persona", DEFAULTS["persona"])
    self.persona: Path | None = (vault / persona) if persona else None
    self.private_paths: list[str] = data.get("private_paths", DEFAULTS["private_paths"])
    self.state_dir = vault / ".taste-engine"

  def agent_order(self, step: str) -> list[str]:
    """Agents to try for `step`: its override first, then the global ordered list. Deduplicated."""
    legacy = self.agents.get(step) if step != "fallback" else None
    order: list[str] = []
    for name in _as_list(self.steps.get(step)) + _as_list(legacy) + self.agent_list:
      if name not in order:
        order.append(name)
    return order


def _legacy_list(mapping: dict) -> list[str]:
  fallback = mapping.get("fallback", [])
  return [fallback] if isinstance(fallback, str) else list(fallback)


def _as_list(value) -> list[str]:
  if not value:
    return []
  return [value] if isinstance(value, str) else list(value)


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
