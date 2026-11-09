"""Actions layer: the human gate.

Generated notes start as `pending_review`. Only the owner moves them on:
pending_review → approved → published, or → rejected.
"""

from __future__ import annotations

from pathlib import Path
import re

from noetic.knowledge.notes import ADR_STATUS_FLOW, STATUS_FLOW, set_status, verify_approval_hash


class GateClosed(Exception):
  pass


def status_of(path: Path) -> str | None:
  if not path.exists():
    return None
  m = re.search(r"^status:\s*(\S+)", path.read_text(encoding="utf-8"), re.M)
  return m.group(1) if m else None


def approve(path: Path, note: str = "") -> None:
  text = path.read_text(encoding="utf-8") if path.exists() else ""
  if "type: adr" in text:
    set_status(path, "accepted", note)
  else:
    set_status(path, "approved", note)


def reject(path: Path, reason: str = "") -> None:
  set_status(path, "rejected", reason)


def require_approved(path: Path, verify_hash: bool = False) -> None:
  """Call before any public or irreversible action."""
  status = status_of(path)
  if status not in ("approved", "accepted"):
    raise GateClosed(f"{path.name} is '{status}'; approve it first (noetic approve \"{path}\")")
  if verify_hash and not verify_approval_hash(path):
    raise GateClosed(f"{path.name} approval hash mismatch: content was modified after approval")


__all__ = ["ADR_STATUS_FLOW", "STATUS_FLOW", "GateClosed", "approve", "reject", "require_approved", "status_of", "verify_approval_hash"]
