"""replicate: framework + reference sites → build brief → (optional) code on a new branch.

Steal the mechanism, transform the expression. With --build, an agent
implements the brief in a target git repo on a fresh branch. It never commits:
the owner reviews the diff (the human gate).
"""

from pathlib import Path

from noetic.gates.git import GitError, changed_files, current_branch, head, new_work_branch
from noetic.knowledge import context, notes
from noetic.orchestration.registry import arg, pipeline
from noetic.orchestration.run import PipelineError
from noetic.orchestration.steps import agent_step
from noetic.tools import prompts


@pipeline("replicate", kind="code", help="reference sites → build brief (→ code with --build)", args=[
  arg("framework", help="framework slug, e.g. steal-like-an-artist"),
  arg("urls", nargs="+", help="reference URLs (awwwards, dribbble, portfolios…)"),
  arg("--goal", default="", help="what you want to build"),
  arg("--build", help="path to a git repo: an agent implements the brief on a new branch (never commits)"),
  arg("--build-agent", help="force the build agent (default: config steps.build, then the ordered agents list)"),
])
def replicate(run, a):
  cfg = run.cfg
  fw_file = cfg.frameworks / f"{a['framework']}.md"
  if not fw_file.exists():
    close = [p.stem for p in cfg.frameworks.glob("*.md") if a["framework"].split("-")[0] in p.stem]
    raise PipelineError("FRAMEWORK_NOT_FOUND", a["framework"], did_you_mean=close)

  # The framework note is the tool here: it becomes the agent's instructions.
  prompt = prompts.render(cfg, "deconstruct", {
    "framework": context.read_body(fw_file, context.BUDGET["framework"]),
    "references": "\n".join(f"- {u}" for u in a["urls"]),
    "goal": a.get("goal") or "a component/section inspired by these references",
  })
  spec = run.step("deconstruct", lambda: agent_step(run, "deconstruct", "deconstruct", prompt, "ui_spec",
                                                    agent=a.get("agent"), web=True, timeout=1500))

  def write_brief():
    brief = notes.build_brief(cfg, spec, a["framework"], run.agent_for("deconstruct"), run.id)
    notes.append_application(fw_file, "code", brief)
    return run.output(brief)
  brief_rel = run.step("write-brief", write_brief)

  if not a.get("build"):
    return [brief_rel]

  repo = Path(a["build"]).expanduser().resolve()

  def prepare():
    try:
      branch = new_work_branch(repo, f"taste-engine/{spec['slug'] or 'build'}-{run.id[-4:]}")
      return {"branch": branch, "head": head(repo)}
    except GitError as exc:
      raise PipelineError(exc.code, exc.detail) from exc
  base = run.step("prepare-repo", prepare)
  branch = base["branch"]

  def enforce_contract(d: dict) -> list[str]:
    """Check the agent's work against git, not against its own report."""
    if current_branch(repo) != branch:
      raise PipelineError("CONTRACT_VIOLATION", f"agent switched branch to '{current_branch(repo)}' (expected {branch})")
    if head(repo) != base["head"]:
      raise PipelineError("CONTRACT_VIOLATION", "agent committed; HEAD moved. Inspect the repo before continuing")
    actual = changed_files(repo)
    reported = {f.replace("\\", "/").removeprefix("./") for f in d["files_changed"]}
    if reported != actual:
      d["harness_notes"] = d.get("harness_notes", []) + [
        f"HARNESS: files_changed corrected to git's list. Unreported: {sorted(actual - reported) or '-'}; "
        f"reported but unchanged: {sorted(reported - actual) or '-'}"]
      d["files_changed"] = sorted(actual)
    return []

  build_prompt = prompts.render_raw("build", {"brief": (cfg.vault / brief_rel).read_text(encoding="utf-8")})
  report = run.step("build", lambda: agent_step(run, "build", "build", build_prompt, "build_report",
                                               agent=a.get("build_agent"), write=True, cwd=repo, timeout=3600,
                                               extra_check=enforce_contract))

  def finish():
    brief = cfg.vault / brief_rel
    section = notes.build_report_section(report, run.agent_for("build"), repo, branch)
    brief.write_text(brief.read_text(encoding="utf-8") + section, encoding="utf-8")
    return [brief_rel, f"{repo} @ {branch} (uncommitted)"]
  return run.step("report", finish)
