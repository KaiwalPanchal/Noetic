"""Knowledge layer: the project / quest / log registry.

Reads the Noetic wiki as plain markdown and returns plain dicts. No LLM, no
network. Every read goes through the policy gate, which blocks the private
profile directory (<overmind>/wiki/profile/) and anything in config
`private_paths`.

Project pages (`<overmind>/wiki/projects/*.md`) carry YAML frontmatter:
  name, status (active|parked|blocked|done), goal, competency, repo,
  next_action, last_touched (YYYY-MM-DD), gate (optional free text)
Missing keys are tolerated and reported (`incomplete`, `missing`).
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import re

import yaml

from noetic.knowledge.config import Config
from noetic.knowledge.context import is_private
from noetic.gates.policy_gate import SecurityViolation, is_profile_path, validate_overmind_path

STATUSES = ("active", "parked", "blocked", "done")
REQUIRED = ("name", "status", "goal", "next_action", "last_touched")
STALE_AFTER_DAYS = 14
DONE_QUEST = {"done", "complete", "completed", "closed", "verified", "shipped"}
_SKIP_STEMS = {"readme", "index", "_index"}


def _private(cfg: Config, path: Path) -> bool:
  try:
    return is_private(cfg, cfg.vault / path.resolve().relative_to(cfg.vault.resolve()))
  except ValueError:
    return True  # outside the vault: treat as unreadable


def read_page(cfg: Config, path: Path | str) -> str:
  """Policy-gated read of one wiki page (vault-confined, profile-blocked)."""
  if cfg.overmind is None:
    raise SecurityViolation("OverMind path is not configured.")
  safe = validate_overmind_path(path, cfg.vault, cfg.overmind)
  if _private(cfg, safe):
    raise SecurityViolation("Path is listed in private_paths.")
  return safe.read_text(encoding="utf-8", errors="replace")


def _pages(cfg: Config, *parts: str, pattern: str = "*.md") -> list[Path]:
  if cfg.overmind is None:
    return []
  folder = cfg.overmind.joinpath(*parts)
  if not folder.is_dir() or is_profile_path(folder, cfg.overmind):
    return []
  out = []
  for f in sorted(folder.glob(pattern)):
    try:
      validate_overmind_path(f, cfg.vault, cfg.overmind)
    except SecurityViolation:
      continue
    if f.is_file() and not _private(cfg, f):
      out.append(f)
  return out


def split_frontmatter(text: str) -> tuple[dict, str]:
  """(frontmatter dict, body). Bad or missing YAML gives ({}, text)."""
  if not text.startswith("---"):
    return {}, text
  end = text.find("\n---", 3)
  if end == -1:
    return {}, text
  try:
    data = yaml.safe_load(text[3:end]) or {}
  except yaml.YAMLError:
    return {}, text[end + 4:]
  return (data if isinstance(data, dict) else {}), text[end + 4:]


def _date(value) -> date | None:
  if isinstance(value, datetime):
    return value.date()
  if isinstance(value, date):
    return value
  if isinstance(value, str):
    try:
      return date.fromisoformat(value.strip()[:10])
    except ValueError:
      return None
  return None


def _text(value) -> str:
  return "" if value is None else str(value).strip()


def _rel(cfg: Config, f: Path) -> str:
  return f.relative_to(cfg.vault).as_posix()


def load_projects(cfg: Config, today: date | None = None) -> list[dict]:
  today = today or date.today()
  rows = []
  for f in _pages(cfg, "wiki", "projects"):
    if f.stem.lower() in _SKIP_STEMS:
      continue
    fm, _ = split_frontmatter(read_page(cfg, f))
    touched = _date(fm.get("last_touched"))
    status = _text(fm.get("status")).lower()
    missing = [k for k in REQUIRED if not _text(fm.get(k))]
    if status and status not in STATUSES and "status" not in missing:
      missing.append("status")
    if _text(fm.get("last_touched")) and touched is None and "last_touched" not in missing:
      missing.append("last_touched")
    rows.append({
        "name": _text(fm.get("name")) or f.stem,
        "status": status,
        "goal": _text(fm.get("goal")),
        "competency": _text(fm.get("competency")),
        "repo": _text(fm.get("repo")),
        "next_action": _text(fm.get("next_action")),
        "last_touched": touched.isoformat() if touched else "",
        "stale_days": (today - touched).days if touched else None,
        "gate": _text(fm.get("gate")),
        "incomplete": bool(missing),
        "missing": missing,
        "file": _rel(cfg, f),
    })
  return rows


def is_stale(project: dict) -> bool:
  return (project["status"] in ("active", "blocked") and project["stale_days"] is not None
          and project["stale_days"] > STALE_AFTER_DAYS)


def _body_field(body: str, label: str) -> str:
  m = re.search(rf"^[ \t>*_-]*{label}[ \t]*\**[ \t]*:\**[ \t]*(.+?)\s*$", body, re.I | re.M)
  return m.group(1).strip(" *_") if m else ""


def load_quests(cfg: Config, today: date | None = None) -> list[dict]:
  today = today or date.today()
  rows = []
  for f in _pages(cfg, "wiki", "quests", pattern="QUEST-*.md"):
    fm, body = split_frontmatter(read_page(cfg, f))
    qid = _text(fm.get("id")) or (re.match(r"QUEST-\d+", f.stem, re.I) or re.match(r".*", f.stem)).group(0).upper()
    status = (_text(fm.get("status")) or _body_field(body, "status") or "unknown").lower()
    due = _date(fm.get("due")) or _date(_body_field(body, "due"))
    xp = _text(fm.get("proposed_xp")) or _body_field(body, "proposed xp")
    xp_num = re.match(r"\d+", xp)
    rows.append({
        "id": qid,
        "status": status,
        "due": due.isoformat() if due else "",
        "overdue": bool(due and due < today and status not in DONE_QUEST),
        "proposed_xp": int(xp_num.group(0)) if xp_num else None,
        "file": _rel(cfg, f),
    })
  return rows


def log_tail(cfg: Config, lines: int = 20) -> list[str]:
  """Last non-blank lines of the newest wiki/log/*.md (monthly files sort by name)."""
  pages = _pages(cfg, "wiki", "log")
  if not pages:
    return []
  body = split_frontmatter(read_page(cfg, pages[-1]))[1]
  return [l.rstrip() for l in body.splitlines() if l.strip()][-lines:]
