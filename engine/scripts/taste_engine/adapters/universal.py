"""AGENTS.md: the cross-agent standard instruction file (read by Codex and many others)."""

from __future__ import annotations

from pathlib import Path

from .base import Adapter, Canonical, OutFile, block


class UniversalAdapter(Adapter):
  name = "universal"

  def detect(self, vault: Path) -> bool:
    return (vault / "AGENTS.md").exists()

  def render(self, canon: Canonical) -> list[OutFile]:
    return [OutFile("AGENTS.md", block(canon), "block", "# Agent instructions", self.name)]
