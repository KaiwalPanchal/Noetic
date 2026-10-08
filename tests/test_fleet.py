"""Phase 5 fleet: repo telemetry, daily librarian, delegate worker loop (agent mocked)."""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from overmind.agents.runners import AgentResult
from overmind.knowledge import repos
from overmind.knowledge.config import CONFIG_NAME, Config
from overmind.orchestration import steps as steps_mod
from overmind.orchestration.run import PipelineError, Run
from workflows.fleet import librarian as lib
from workflows.fleet.delegate import delegate


def git(repo: Path, *a: str) -> str:
  return subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *a],
                        capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
  r = tmp_path / "proj"
  r.mkdir()
  git(r, "init", "-q")
  (r / "a.txt").write_text("one\n", encoding="utf-8")
  git(r, "add", ".")
  git(r, "commit", "-qm", "init")
  return r


@pytest.fixture
def fvault(tmp_path: Path, repo: Path) -> Config:
  v = tmp_path / "fv"
  (v / "OverMind" / "wiki" / "projects").mkdir(parents=True)
  (v / "inbox").mkdir()
  (v / "taste-engine").mkdir()
  cfgdata = {"owner": "T", "paths": {"overmind": "OverMind"}, "agents": ["claude"]}
  (v / CONFIG_NAME).write_text(json.dumps(cfgdata), encoding="utf-8")
  (v / "OverMind" / "wiki" / "projects" / "proj.md").write_text(
      f"---\nname: Proj\nstatus: active\ngoal: G1\ncompetency: C1\nrepo: {repo.as_posix()}\nnext_action: x\nlast_touched: 2026-09-01\n---\n# Proj\n",
      encoding="utf-8")
  return Config(v, cfgdata)


def test_repo_telemetry_reports_dirty_and_last_commit(fvault, repo):
  (repo / "a.txt").write_text("two\n", encoding="utf-8")
  (repo / "new.txt").write_text("n\n", encoding="utf-8")
  (row,) = repos.load_repo_telemetry(fvault)
  assert row["ok"] and row["dirty"] == 1 and row["untracked"] == 1 and "init" in row["last_commit"]
  assert "1 modified, 1 untracked" in repos.render_repo_telemetry([row])


def test_repo_telemetry_bad_path_does_not_raise(tmp_path):
  assert repos.repo_status(tmp_path / "nope")["error"] == "path not found"
  assert repos.repo_status(tmp_path)["error"] == "not a git repo"


def test_librarian_flags_empty_and_duplicates_suggests_links_and_changes_nothing(fvault):
  v = fvault.vault
  (v / "Compounding Interest.md").write_text("# Compounding\nstuff\n", encoding="utf-8")
  (v / "inbox" / "a.md").write_text("Notes on Compounding Interest and habits\n", encoding="utf-8")
  (v / "inbox" / "b.md").write_text("Notes on Compounding Interest and habits\n", encoding="utf-8")
  (v / "inbox" / "c.md").write_text("", encoding="utf-8")
  before = {p.name: p.read_text(encoding="utf-8") for p in (v / "inbox").glob("*.md")}
  digest = lib.run_librarian(fvault)
  text = digest.read_text(encoding="utf-8")
  assert "status: pending_review" in text and "[[Compounding Interest]]" in text
  assert "duplicate of a.md" in text and "empty" in text
  assert {p.name: p.read_text(encoding="utf-8") for p in (v / "inbox").glob("*.md")} == before


def test_librarian_runs_at_most_once_per_24h(fvault):
  assert lib.run_librarian(fvault) is not None
  assert lib.run_librarian(fvault) is None
  assert lib.run_librarian(fvault, force=True) is not None
  assert lib.due(fvault, datetime.now() + timedelta(hours=25))


def _fake_agent(monkeypatch, repo: Path, edits: list[str]):
  """Each call 'edits' the repo with the next content, like a worker agent would."""
  calls = []

  def fake(agent, prompt, schema, **kw):
    calls.append(prompt)
    (repo / "a.txt").write_text(edits[min(len(calls), len(edits)) - 1], encoding="utf-8")
    return AgentResult(agent, True, data={"summary": "s", "files_changed": ["a.txt"], "done": True, "harness_notes": []})
  monkeypatch.setattr(steps_mod, "run_agent", fake)
  return calls


def test_delegate_loops_on_failing_tests_then_passes(fvault, repo, monkeypatch):
  calls = _fake_agent(monkeypatch, repo, ["bad\n", "good\n"])
  test = f'{sys.executable} -c "import sys; sys.exit(0 if open(\'a.txt\').read().strip()==\'good\' else 1)"'
  run = Run(fvault, "delegate", {"project": "Proj", "task": "fix a"})
  out = delegate(run, {"project": "Proj", "task": "fix a", "test": test, "max_iterations": 3, "agent": "claude"})
  assert len(calls) == 2 and "FAILED" in calls[1]
  assert git(repo, "branch", "--show-current").startswith("overmind/proj-fix-a")
  assert git(repo, "log", "--oneline").count("\n") == 0  # nothing committed
  log = (fvault.vault / "OverMind" / "wiki" / "log").glob("*.md")
  assert "complete" in next(log).read_text(encoding="utf-8") and out


def test_delegate_refuses_dirty_repo_and_unknown_project(fvault, repo, monkeypatch):
  _fake_agent(monkeypatch, repo, ["x\n"])
  (repo / "a.txt").write_text("dirty\n", encoding="utf-8")
  with pytest.raises(PipelineError) as e:
    delegate(Run(fvault, "delegate", {"project": "Proj", "task": "t"}), {"project": "Proj", "task": "t", "agent": "claude"})
  assert "DIRTY_WORKTREE" in str(e.value)
  with pytest.raises(PipelineError) as e:
    delegate(Run(fvault, "delegate", {"project": "Nope", "task": "t"}), {"project": "Nope", "task": "t"})
  assert "UNKNOWN_PROJECT" in str(e.value)
