"""delegate: an agent works on a task inside a registered project's repo, on its own branch.

Loop: agent edits -> harness runs the test command -> on failure the output is fed back, up to
--max-iterations. Branch isolation like `replicate --build`: the agent never commits; you review the diff.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import subprocess

from overmind.gates.git import GitError, changed_files, current_branch, head, new_work_branch
from overmind.knowledge import registry, repos
from overmind.knowledge.config import slugify
from overmind.orchestration.registry import arg, pipeline
from overmind.orchestration.run import PipelineError
from overmind.orchestration.steps import agent_step
from overmind.tools import prompts

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
  arg("--max-iterations", type=int, default=3, help="attempts before giving up (default 3)"),
])
def delegate(run, a) -> list[str]:
  cfg = run.cfg
  proj = run.step("resolve", lambda: find_project(cfg, a["project"]))
  repo = repos.resolve_repo(cfg, proj["repo"])
  test_cmd = a.get("test") or ""
  limit = max(1, int(a.get("max_iterations") or 3))

  def prepare():
    try:
      branch = new_work_branch(repo, f"overmind/{slugify(proj['name'])[:24]}-{slugify(a['task'])[:24]}-{run.id[-4:]}")
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

  feedback, report, tests = "", None, None
  for i in range(1, limit + 1):
    prompt = prompts.render_raw("delegate", {"task": a["task"], "feedback": feedback})
    report = run.step(f"attempt-{i}", lambda p=prompt, n=i: agent_step(
        run, f"attempt-{n}", "delegate", p, "delegate_report", agent=a.get("agent"), write=True, cwd=repo,
        timeout=3600, extra_check=enforce_contract))
    if not test_cmd:
      break
    tests = run.step(f"tests-{i}", lambda: run_tests(test_cmd, repo))
    if tests["passed"]:
      break
    feedback = f"The test command `{test_cmd}` FAILED after your last attempt. Fix the cause. Output (tail):\n{tests['output']}"

  ok = bool(report and report["done"] and (tests is None or tests["passed"]))
  suffix = "" if tests is None else (" (tests pass)" if tests["passed"] else " (tests FAILING)")
  entry = f"delegate {proj['name']}: {a['task'][:80]} -> {'complete' if ok else 'needs review'} on `{base['branch']}`{suffix}"
  logged = append_log(cfg, entry)
  print(f"\n{entry}\n  repo: {repo}  (changes are uncommitted; review the diff)")
  return ([logged] if logged else []) + [f"{repo} @ {base['branch']} (uncommitted)"]
