"""Codex CLI: reads AGENTS.md from the repo root. Custom prompts live at user level
(~/.codex/prompts), outside the vault, so they are documented but never generated."""

from __future__ import annotations

from .universal import UniversalAdapter


class CodexAdapter(UniversalAdapter):
  name = "codex"
  notes = ("codex: reads AGENTS.md (generated). Custom prompts are user-level (~/.codex/prompts) and are not written; "
           "commands are reachable through the command index in AGENTS.md.",)
