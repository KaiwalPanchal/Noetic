"""Tools layer: owned prompts (12-factor #2).

Prompts are plain markdown in engine/prompts/ with {{placeholders}}. Every
prompt except raw ones starts with _preamble.md (ground rules + the owner's
interests and taste).
"""

from __future__ import annotations

import json
import re

from taste_engine.knowledge import context
from taste_engine.knowledge.config import PROMPTS_DIR, SCHEMAS_DIR, Config

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def fill(template: str, values: dict) -> str:
  return _PLACEHOLDER.sub(lambda m: str(values.get(m.group(1), "")), template)


def render(cfg: Config, name: str, values: dict | None = None) -> str:
  base = {
    "owner": cfg.owner, "interests": context.interests(cfg), "taste": context.taste(cfg),
    "x_limit": str(cfg.x_char_limit), "fix_note": "",
  }
  merged = {**base, **(values or {})}
  merged["preamble"] = fill((PROMPTS_DIR / "_preamble.md").read_text(encoding="utf-8"), merged)
  return fill((PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8"), merged)


def render_raw(name: str, values: dict) -> str:
  """A prompt without the preamble (e.g. build.md, which runs inside another repo)."""
  return fill((PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8"), values)


def schema(name: str) -> dict:
  return json.loads((SCHEMAS_DIR / f"{name}.json").read_text(encoding="utf-8"))
