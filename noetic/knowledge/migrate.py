"""One-time vault migration: `taste-engine.config.json` -> `noetic.config.json`, `.taste-engine/` -> `.noetic/`.

Idempotent and non-destructive: it only renames, never deletes, and skips (and says so) when both the old and
the new name exist, since merging two states is a human call.
"""

from __future__ import annotations

from pathlib import Path

from noetic.knowledge.config import CONFIG_NAME, LEGACY_CONFIG_NAME, LEGACY_STATE_DIR_NAME, STATE_DIR_NAME


def migrate(vault: Path, dry_run: bool = False) -> list[str]:
  """Rename legacy files in `vault`. Returns a human-readable list of what was (or would be) done."""
  actions: list[str] = []
  for old_name, new_name, kind in ((LEGACY_CONFIG_NAME, CONFIG_NAME, "config"),
                                   (LEGACY_STATE_DIR_NAME, STATE_DIR_NAME, "state folder")):
    old, new = vault / old_name, vault / new_name
    if not old.exists():
      continue
    if new.exists():
      actions.append(f"SKIP {kind}: both {old_name} and {new_name} exist; merge by hand")
      continue
    actions.append(f"{'would rename' if dry_run else 'renamed'} {kind}: {old_name} -> {new_name}")
    if not dry_run:
      old.rename(new)
  return actions or ["nothing to migrate"]
