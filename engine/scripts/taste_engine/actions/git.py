"""Actions layer: git work in a target repo (reversible only, never commits or pushes)."""

from __future__ import annotations

from pathlib import Path
import subprocess


class GitError(Exception):
  def __init__(self, code: str, detail: str):
    super().__init__(f"{code}: {detail}")
    self.code, self.detail = code, detail


def git(repo: Path, *args: str) -> str:
  proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
  if proc.returncode != 0:
    raise GitError("GIT_FAILED", proc.stderr.strip()[-300:])
  return proc.stdout.strip()


def new_work_branch(repo: Path, name: str) -> str:
  """Check the repo is clean, then branch off so the agent's changes are isolated."""
  if not (repo / ".git").exists():
    raise GitError("NOT_A_GIT_REPO", f"{repo}: run `git init` there first")
  if git(repo, "status", "--porcelain"):
    raise GitError("DIRTY_WORKTREE", "commit or stash the target repo's changes first")
  git(repo, "checkout", "-b", name)
  return name
