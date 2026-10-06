"""Claude Code: CLAUDE.md block, .claude/commands/*.md, .claude/agents/*.md."""

from __future__ import annotations

from pathlib import Path

from .base import Adapter, Canonical, OutFile, block, md_with_header, yaml_str


class ClaudeAdapter(Adapter):
  name = "claude"
  managed_dirs = (".claude/commands", ".claude/agents")

  def __init__(self, include_agents: bool = True):
    self.include_agents = include_agents

  def detect(self, vault: Path) -> bool:
    return (vault / ".claude").is_dir() or (vault / "CLAUDE.md").exists()

  def render(self, canon: Canonical) -> list[OutFile]:
    out = [OutFile("CLAUDE.md", block(canon), "block", "# Vault instructions", self.name)]
    for c in canon.commands:
      fm = c.raw_frontmatter or f"description: {yaml_str(c.description)}"
      out.append(OutFile(f".claude/commands/{c.name}.md", md_with_header(fm, [(c.source, c.text)], c.body),
                         adapter=self.name))
    if self.include_agents:
      for a in canon.agents:
        fm = f"name: {a.slug}\ndescription: {yaml_str(a.description)}"
        out.append(OutFile(f".claude/agents/{a.slug}.md", md_with_header(fm, [(a.source, a.text)], a.body),
                           adapter=self.name))
    return out
