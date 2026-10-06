"""Tools layer: owned prompts (12-factor #2).

Prompts are plain markdown in engine/prompts/ with {{placeholders}}.
Every prompt starts with _contract.md, the strict agent contract: follow only
harness instructions, use only the given tools and context, add no logic of
your own, and report gaps in `harness_notes`. Non-raw prompts then include
_preamble.md (step rules + the owner's interests and taste).
"""

from __future__ import annotations

import json
import re

from taste_engine.knowledge import context
from taste_engine.knowledge.config import AGENTS_DIR, PROMPTS_DIR, SCHEMAS_DIR, Config

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def fill(template: str, values: dict) -> str:
  return _PLACEHOLDER.sub(lambda m: str(values.get(m.group(1), "")), template)


def contract() -> str:
  return (PROMPTS_DIR / "_contract.md").read_text(encoding="utf-8")


def render(cfg: Config, name: str, values: dict | None = None) -> str:
  base = {
    "owner": cfg.owner, "interests": context.interests(cfg), "taste": context.taste(cfg),
    "x_limit": str(cfg.x_char_limit), "fix_note": "",
  }
  merged = {**base, **(values or {})}
  merged["preamble"] = fill((PROMPTS_DIR / "_preamble.md").read_text(encoding="utf-8"), merged)
  return contract() + "\n" + fill((PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8"), merged)


def render_raw(name: str, values: dict) -> str:
  """A prompt with the contract but without the preamble (e.g. build.md, which runs inside another repo)."""
  return contract() + "\n" + fill((PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8"), values)


def schema(name: str) -> dict:
  return json.loads((SCHEMAS_DIR / f"{name}.json").read_text(encoding="utf-8"))


def agent_contract(name: str) -> str:
  """The canonical, provider-neutral role contract in engine/agents/<name>.md (frontmatter stripped)."""
  text = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")
  if text.startswith("---"):
    end = text.find("\n---", 3)
    if end != -1:
      text = text[end + 4:]
  return text.strip()
