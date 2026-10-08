"""Gates layer: deterministic taste gate.

Rejects generic, bloated, or off-taste output before persistence, using
owner-defined rules in .noetic/taste/ (dogmas.md, anti-patterns.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from noetic.knowledge.config import Config


@dataclass
class TasteRules:
  dogmas: str
  phrases: list[str]
  patterns: list[re.Pattern]
  required: list[str]


def load(cfg: Config) -> TasteRules | None:
  """Load active taste rules from <state_dir>/taste/. Returns None if no rule files exist."""
  taste_dir = cfg.state_dir / "taste"
  dogmas_file = taste_dir / "dogmas.md"
  anti_file = taste_dir / "anti-patterns.md"

  if not dogmas_file.exists() and not anti_file.exists():
    return None

  dogmas = dogmas_file.read_text(encoding="utf-8").strip() if dogmas_file.exists() else ""

  phrases: list[str] = []
  patterns: list[re.Pattern] = []
  required: list[str] = []

  if anti_file.exists():
    content = anti_file.read_text(encoding="utf-8")
    current_section = None
    for raw_line in content.splitlines():
      line = raw_line.strip()
      if line.startswith("## "):
        header = line[3:].strip().lower()
        if "phrase" in header:
          current_section = "phrases"
        elif "pattern" in header:
          current_section = "patterns"
        elif "required" in header:
          current_section = "required"
        else:
          current_section = None
        continue

      if not (line.startswith("- ") or line.startswith("* ")):
        continue

      bullet_text = line[2:].strip()
      if not bullet_text:
        continue

      if current_section == "phrases":
        phrases.append(bullet_text)
      elif current_section == "patterns":
        # Extract regex from backticks if present
        m = re.search(r"`([^`]+)`", bullet_text)
        pat_str = m.group(1) if m else bullet_text
        try:
          patterns.append(re.compile(pat_str, re.IGNORECASE))
        except re.error as exc:
          raise ValueError(f"invalid regex in bullet '{line}': {exc}") from exc
      elif current_section == "required":
        required.append(bullet_text)

  return TasteRules(dogmas=dogmas, phrases=phrases, patterns=patterns, required=required)


def violations(rules: TasteRules, data: Any) -> list[str]:
  """Walk every string in nested data and return exact, actionable violation messages."""
  viols: list[str] = []
  found_required = {req: False for req in rules.required}

  def walk(val: Any, path: str):
    if isinstance(val, dict):
      for k, v in val.items():
        if k == "harness_notes":
          continue
        walk(v, f"{path}.{k}")
    elif isinstance(val, list):
      for i, item in enumerate(val):
        walk(item, f"{path}[{i}]")
    elif isinstance(val, str):
      val_lower = val.lower()
      for phrase in rules.phrases:
        if phrase.lower() in val_lower:
          viols.append(f'taste: banned phrase "{phrase}" in {path}')
      for pat in rules.patterns:
        if pat.search(val):
          viols.append(f'taste: banned pattern "{pat.pattern}" in {path}')
      for req in rules.required:
        if req.lower() in val_lower:
          found_required[req] = True

  if isinstance(data, (dict, list)):
    walk(data, "$")
  elif isinstance(data, str):
    walk(data, "$")

  for req, found in found_required.items():
    if not found:
      viols.append(f'taste: missing required text "{req}"')

  return viols


def prompt_block(rules: TasteRules) -> str:
  """Construct a prompt block with non-negotiable taste constraints."""
  lines = ["\n## Taste bar (non-negotiable)"]
  if rules.dogmas:
    lines.append(rules.dogmas)
  if rules.phrases or rules.patterns:
    lines.append("\nStrictly avoid the following low-signal phrases and patterns:")
    for p in rules.phrases:
      lines.append(f'- "{p}"')
    for pat in rules.patterns:
      lines.append(f"- `{pat.pattern}`")
  if rules.required:
    lines.append("\nMust include:")
    for r in rules.required:
      lines.append(f'- "{r}"')
  return "\n".join(lines) + "\n"
