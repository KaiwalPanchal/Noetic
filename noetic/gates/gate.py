"""Actions layer: the human gate.

Generated notes start as `pending_review`. Only the owner moves them on:
pending_review → approved → published, or → rejected.
"""

from __future__ import annotations

from pathlib import Path
import re

from noetic.knowledge.notes import STATUS_FLOW, set_status


class GateClosed(Exception):
  pass


def status_of(path: Path) -> str | None:
  m = re.search(r"^status:\s*(\S+)", path.read_text(encoding="utf-8"), re.M)
  return m.group(1) if m else None


def approve(path: Path, note: str = "") -> None:
  set_status(path, "approved", note)


def reject(path: Path, reason: str = "") -> None:
  set_status(path, "rejected", reason)


def require_approved(path: Path) -> None:
  """Call before any public or irreversible action."""
  status = status_of(path)
  if status != "approved":
    raise GateClosed(f"{path.name} is '{status}'; approve it first (pipeline.py approve \"{path}\")")


__all__ = ["STATUS_FLOW", "GateClosed", "approve", "reject", "require_approved", "status_of"]
