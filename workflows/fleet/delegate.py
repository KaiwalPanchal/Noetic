"""delegate: an agent works on a task inside a registered project's repo, on its own branch.

Loop: agent edits -> harness runs the test command -> on failure the output is fed back, up to
--max-iterations. Branch isolation like `replicate --build`: the agent never commits; you review the diff.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import subprocess

from noetic.gates.git import GitError, changed_files, current_branch, head, new_work_branch
from noetic.knowledge import registry, repos
from noetic.knowledge.config import slugify
from noetic.orchestration.loop import Verdict, run_loop
from noetic.orchestration.registry import arg, pipeline
from noetic.orchestration.run import PipelineError
from noetic.orchestration.steps import agent_step
from noetic.tools import prompts

TAIL = 3000


def find_project(cfg, name: str) -> dict:
  rows = registry.load_projects(cfg)
  hit = next((p for p in rows if p["name"].lower() == name.lower() or Path(p["file"]).stem.lower() == name.lower()), None)
  if hit is None:
    raise PipelineError("UNKNOWN_PROJECT", f"'{name}' is not in the project registry ({', '.join(p['name'] for p in rows) or 'empty'})")
  if not hit["repo"]:
    raise PipelineError("NO_REPO", f"project '{hit['name']}' has no `repo` in its frontmatter")
  return hit


def run_tests(command: str, repo: Path, timeout: int = 900) -> dict:
  """Run the test command the owner supplied, inside the repo."""
  try:
    proc = subprocess.run(command, cwd=repo, shell=True, capture_output=True, text=True, timeout=timeout)
  except subprocess.TimeoutExpired:
    return {"passed": False, "output": f"test command timed out after {timeout}s"}
  return {"passed": proc.returncode == 0, "output": (proc.stdout + proc.stderr)[-TAIL:]}


def append_log(cfg, text: str) -> str | None:
  """Append a dated entry to <overmind>/wiki/log/YYYY-MM.md (the Overmind writes its own log)."""
  if cfg.overmind is None:
    return None
  log = cfg.overmind / "wiki" / "log" / f"{date.today():%Y-%m}.md"
  log.parent.mkdir(parents=True, exist_ok=True)
  entry = f"## {date.today().isoformat()} — {text}\n"
  prior = log.read_text(encoding="utf-8").rstrip() if log.exists() else ""
  log.write_text((prior + "\n\n" if prior else "") + entry, encoding="utf-8")
  return str(log.relative_to(cfg.vault))


@pipeline("delegate", kind="code", help="agent works a task in a project's repo on a new branch, looping on tests", args=[
  arg("project", help="project name from the registry (its `repo` field is the target)"),
  arg("task", help="what to do"),
  arg("--test", help="command to run after each attempt"),
  arg("--max-iterations", type=int, default=None, help="attempts before giving up"),
])
def delegate(run, a) -> list[str]:
  cfg = run.cfg
  proj = run.step("resolve", lambda: find_project(cfg, a["project"]))
  repo = repos.resolve_repo(cfg, proj["repo"])
  test_cmd = a.get("test") or ""

  if a.get("max_iterations") is not None:
    limit = max(1, int(a["max_iterations"]))
  else:
    try:
      from noetic.agents.spec import load_specs
      worker_spec = load_specs().get("worker")
      budget_limit = worker_spec.budget.get("max_iterations") if worker_spec else None
    except Exception:
      budget_limit = None
    limit = max(1, int(budget_limit or 3))

  def prepare():
    try:
      branch = new_work_branch(repo, f"noetic/{slugify(proj['name'])[:24]}-{slugify(a['task'])[:24]}-{run.id[-4:]}")
      return {"branch": branch, "head": head(repo)}
    except GitError as exc:
      raise PipelineError(exc.code, exc.detail) from exc
  base = run.step("prepare-repo", prepare)

  def enforce_contract(d: dict) -> list[str]:
    if current_branch(repo) != base["branch"]:
      raise PipelineError("CONTRACT_VIOLATION", f"agent switched branch to '{current_branch(repo)}' (expected {base['branch']})")
    if head(repo) != base["head"]:
      raise PipelineError("CONTRACT_VIOLATION", "agent committed; HEAD moved. Inspect the repo before continuing")
    d["files_changed"] = sorted(changed_files(repo))
    return []

  def act(i: int, feedback: str) -> dict:
    prompt = prompts.render_raw("delegate", {"task": a["task"], "feedback": feedback})
    return agent_step(
        run, f"delegate-act-{i}", "delegate", prompt, "delegate_report", agent=a.get("agent"), write=True, cwd=repo,
        timeout=3600, extra_check=enforce_contract)

  def evaluate(i: int, report: dict) -> Verdict:
    if not test_cmd:
      return Verdict(ok=True)
    tests = run_tests(test_cmd, repo)
    if tests["passed"]:
      return Verdict(ok=True)
    fb = f"The test command `{test_cmd}` FAILED after your last attempt. Fix the cause. Output (tail):\n{tests['output']}"
    return Verdict(ok=False, feedback=fb)

  loop_res = run_loop(run, "delegate", act, evaluate, max_iterations=limit)
  report = loop_res.result
  ok = bool(report and report.get("done") and loop_res.verdict.ok)
  suffix = "" if not test_cmd else (" (tests pass)" if loop_res.verdict.ok else " (tests FAILING)")
  entry = f"delegate {proj['name']}: {a['task'][:80]} -> {'complete' if ok else 'needs review'} on `{base['branch']}`{suffix}"
  logged = append_log(cfg, entry)
  print(f"\n{entry}\n  repo: {repo}  (changes are uncommitted; review the diff)")
  return ([logged] if logged else []) + [f"{repo} @ {base['branch']} (uncommitted)"]

