"""Knowledge layer: live git telemetry for registered project repos (read-only, no LLM)."""

from __future__ import annotations

from pathlib import Path

from noetic.gates.git import GitError, git
from noetic.knowledge import registry
from noetic.knowledge.config import Config


def repo_status(path: Path) -> dict:
  """Branch, uncommitted changes and latest commit of one repo. Never raises on a bad repo."""
  row = {"path": str(path), "ok": False, "branch": "", "dirty": 0, "untracked": 0, "ahead": None, "behind": None,
         "last_commit": "", "last_commit_age": "", "error": ""}
  if not path.is_dir():
    row["error"] = "path not found"
    return row
  if not (path / ".git").exists():
    row["error"] = "not a git repo"
    return row
  try:
    row["branch"] = git(path, "branch", "--show-current") or "(detached)"
    for line in git(path, "status", "--porcelain", "--untracked-files=all").splitlines():
      if line.startswith("??"):
        row["untracked"] += 1
      elif line.strip():
        row["dirty"] += 1
    try:
      ahead, behind = git(path, "rev-list", "--left-right", "--count", "HEAD...@{upstream}").split()
      row["ahead"], row["behind"] = int(ahead), int(behind)
    except GitError:
      pass  # no upstream configured
    try:
      row["last_commit"] = git(path, "log", "-1", "--format=%h %s")
      row["last_commit_age"] = git(path, "log", "-1", "--format=%cr")
    except GitError:
      row["last_commit"] = "(no commits yet)"
    row["ok"] = True
  except GitError as exc:
    row["error"] = exc.detail
  return row


def resolve_repo(cfg: Config, value: str) -> Path:
  """A project's `repo` field: absolute, or relative to the vault."""
  p = Path(value).expanduser()
  return p if p.is_absolute() else (cfg.vault / p)


def load_repo_telemetry(cfg: Config) -> list[dict]:
  """One row per registered project that declares a `repo`, stalest first."""
  rows = []
  for proj in registry.load_projects(cfg):
    if not proj["repo"]:
      continue
    rows.append({"project": proj["name"], "status": proj["status"], "stale_days": proj["stale_days"],
                 **repo_status(resolve_repo(cfg, proj["repo"]))})
  return sorted(rows, key=lambda r: (-(r["stale_days"] if r["stale_days"] is not None else -1), r["project"]))


def render_repo_telemetry(rows: list[dict]) -> str:
  if not rows:
    return "No registered project declares a `repo`."
  out = []
  for r in rows:
    if not r["ok"]:
      out.append(f"{r['project']}: {r['error']} ({r['path']})")
      continue
    sync = "" if r["ahead"] is None else f", ahead {r['ahead']}/behind {r['behind']}"
    changes = f"{r['dirty']} modified, {r['untracked']} untracked" if (r["dirty"] or r["untracked"]) else "clean"
    out.append(f"{r['project']}: {r['branch']} · {changes}{sync} · {r['last_commit']} ({r['last_commit_age']})")
  return "\n".join(out)
