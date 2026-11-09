"""Knowledge layer: vault config. Where everything lives and how the engine is wired.

Finds the vault by locating `noetic.config.json` (or the legacy `taste-engine.config.json`),
checked in this order:
1. the NOETIC_VAULT environment variable (legacy: TASTE_ENGINE_VAULT)
2. the current directory and its parents
3. this script's directory and its parents

Machine state lives in `<vault>/.noetic/` (runs, taste rules, caches). A vault that still has the legacy
names keeps working; `noetic migrate` renames them (see noetic/knowledge/migrate.py).
"""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import re

CONFIG_NAME = "noetic.config.json"
LEGACY_CONFIG_NAME = "taste-engine.config.json"
STATE_DIR_NAME = ".noetic"
LEGACY_STATE_DIR_NAME = ".taste-engine"
ENV_VAULT = "NOETIC_VAULT"
LEGACY_ENV_VAULT = "TASTE_ENGINE_VAULT"


def config_file(vault: Path) -> Path:
  """The vault's config file: the new name, else the legacy one, else where the new one would go."""
  for name in (CONFIG_NAME, LEGACY_CONFIG_NAME):
    if (vault / name).is_file():
      return vault / name
  return vault / CONFIG_NAME


def state_dir_for(vault: Path) -> Path:
  """`.noetic/`, unless only the legacy `.taste-engine/` exists (pre-migration vault)."""
  new, old = vault / STATE_DIR_NAME, vault / LEGACY_STATE_DIR_NAME
  return old if old.is_dir() and not new.exists() else new

# .../noetic/knowledge/config.py → the noetic package; agent contracts live beside the runners.
PACKAGE_DIR = Path(__file__).resolve().parents[1]
AGENTS_DIR = PACKAGE_DIR / "agents"

DEFAULTS = {
  "owner": "Owner",
  "agent": "AI agent",  # display name written into note frontmatter
  "paths": {
    "engine": "taste-engine",
    "frameworks": "frameworks",
    "wiki": None,
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
  # Optional Liminal sidecar service: {"url": "http://localhost:8000", "timeout": 10}
  "liminal": None,
  # Cognitive Compiler & Execution Harness configuration [P0.1, P0.3]
  "schema_version": "1.0.0",
  "default_lenses": ["hats-haircuts-and-tattoos", "boring-technology"],
  "similarity_thresholds": {"identical": 0.85, "cousin": 0.65},
  "embedding_model": {"provider": "openai", "model": "text-embedding-3-small", "version": "1"},
  "budget": {"per_run_usd": 1.00, "max_tokens_per_bundle": 4000},
  "mcp_serve_policy": {"require_approved": True, "verify_hash": True},
}


class Config:
  def __init__(self, vault: Path, data: dict):
    self.vault = vault
    self.owner: str = data.get("owner", DEFAULTS["owner"])
    self.agent: str = data.get("agent", DEFAULTS["agent"])
    paths = {**DEFAULTS["paths"], **data.get("paths", {})}
    self.engine = vault / paths["engine"]
    self.frameworks = vault / paths["frameworks"]
    wiki_path = paths.get("wiki") or paths.get("overmind")
    self.wiki: Path | None = (vault / wiki_path) if wiki_path else None
    self.overmind: Path | None = self.wiki  # Backward-compatible alias
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
    self.state_dir = state_dir_for(vault)

    import os
    env_url = os.environ.get("NOETIC_LIMINAL_URL")
    lim_cfg = data.get("liminal", DEFAULTS["liminal"])
    if isinstance(lim_cfg, dict):
      self.liminal_url: str | None = env_url or lim_cfg.get("url")
      self.liminal_timeout: int = int(lim_cfg.get("timeout", 10))
    elif isinstance(lim_cfg, str):
      self.liminal_url: str | None = env_url or lim_cfg
      self.liminal_timeout: int = 10
    else:
      self.liminal_url: str | None = env_url or None
      self.liminal_timeout: int = 10

    # Cognitive Compiler & Execution Harness [P0.1, P0.3]
    self.schema_version: str = str(data.get("schema_version", DEFAULTS["schema_version"]))
    self.default_lenses: list[str] = list(data.get("default_lenses", DEFAULTS["default_lenses"]))
    self.similarity_thresholds: dict = {**DEFAULTS["similarity_thresholds"], **data.get("similarity_thresholds", {})}
    self.embedding_model: dict = {**DEFAULTS["embedding_model"], **data.get("embedding_model", {})}
    self.budget: dict = {**DEFAULTS["budget"], **data.get("budget", {})}
    self.mcp_serve_policy: dict = {**DEFAULTS["mcp_serve_policy"], **data.get("mcp_serve_policy", {})}

  def model_for(self, step: str, agent: str) -> str | None:
    """Return model configured for (step, agent), or agent level, or None."""
    # Check per-step agent override e.g. models.ingest.extract
    step_models = self.models.get(step)
    if isinstance(step_models, dict):
      if agent in step_models:
        return step_models[agent]
    elif isinstance(step_models, str):
      return step_models
    return self.models.get(agent)

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
    if config_file(folder).is_file():
      return folder
  return None


def find_vault() -> Path:
  for var in (ENV_VAULT, LEGACY_ENV_VAULT):
    env = os.environ.get(var)
    if env and config_file(Path(env)).is_file():
      return Path(env)
  for start in (Path.cwd(), Path(__file__).resolve().parent):
    found = _search_up(start)
    if found:
      return found
  raise SystemExit(
    f"Could not find {CONFIG_NAME}. Run `noetic install --vault <path>` first, "
    f"or set {ENV_VAULT}."
  )


def load_config() -> Config:
  vault = find_vault()
  data = json.loads(config_file(vault).read_text(encoding="utf-8"))
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
