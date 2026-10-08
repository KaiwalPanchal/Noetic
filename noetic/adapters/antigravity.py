"""Antigravity: skill folders (.agent/skills/<name>/SKILL.md, name + description frontmatter)."""

from __future__ import annotations

from pathlib import Path

from .base import Adapter, Canonical, OutFile, md_with_header, yaml_str

SKILLS = ".agent/skills"


class AntigravityAdapter(Adapter):
  name = "antigravity"
  managed_dirs = (SKILLS,)

  def detect(self, vault: Path) -> bool:
    return (vault / ".agent").is_dir()

  def _skill(self, name: str, description: str, sources, body: str) -> OutFile:
    fm = f"name: {name}\ndescription: {yaml_str(description)}"
    return OutFile(f"{SKILLS}/{name}/SKILL.md", md_with_header(fm, sources, body), adapter=self.name)

  def render(self, canon: Canonical) -> list[OutFile]:
    out = [self._skill("overmind", "Vault constitution and command index for the Noetic taste engine.",
                       canon.sources(), canon.block_body())]
    for c in canon.commands:
      out.append(self._skill(f"overmind-{c.slug}", c.description, [(c.source, c.text)], c.body))
    for a in canon.agents:
      out.append(self._skill(f"overmind-agent-{a.slug}", a.description, [(a.source, a.text)], a.body))
    return out
