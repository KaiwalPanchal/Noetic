"""Gemini CLI: GEMINI.md block and .gemini/commands/<name>.toml (description + prompt)."""

from __future__ import annotations

import json
from pathlib import Path

from .base import Adapter, Canonical, OutFile, block, header_text


def toml_multiline(body: str) -> str:
  """A TOML multi-line string carrying `body` exactly."""
  triple = "'" * 3
  if triple not in body and not body.endswith("'") and "\r" not in body:
    return f"{triple}\n{body}{triple}"
  esc = body.replace("\\", "\\\\").replace('"""', '\\"\\"\\"').replace("\r", "\\r")
  if esc.endswith('"'):
    esc = esc[:-1] + '\\"'
  return f'"""\n{esc}"""'


class GeminiAdapter(Adapter):
  name = "gemini"
  managed_dirs = (".gemini/commands",)

  def detect(self, vault: Path) -> bool:
    return (vault / ".gemini").is_dir() or (vault / "GEMINI.md").exists()

  def render(self, canon: Canonical) -> list[OutFile]:
    out = [OutFile("GEMINI.md", block(canon), "block", "# Vault instructions", self.name)]
    for c in canon.commands:
      text = (f"# {header_text([(c.source, c.text)])}\n"
              f"description = {json.dumps(c.description, ensure_ascii=False)}\n"
              f"prompt = {toml_multiline(c.body)}\n")
      out.append(OutFile(f".gemini/commands/{c.name}.toml", text, adapter=self.name))
    return out
