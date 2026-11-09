"""replicate: framework + reference sites → build brief → (optional) code on a new branch.

Mode A Cognitive Stacking Enhancement:
- Supports single or multiple stacked frameworks (backward-compatible)
- Synthesizes stacked charter using stack_frameworks logic [R1+R2]
- Injects harmonized heuristics into the deconstruct prompt
- Writes Build Brief note including Dialectic Trade-off Matrix if tensions exist
- Preserves the ephemeral git branch isolation and head(repo) invariant check
"""

from pathlib import Path

from noetic.gates.git import GitError, changed_files, current_branch, head, new_work_branch
from noetic.knowledge import context, notes
from noetic.knowledge.stack import stack_frameworks_logic
from noetic.orchestration.registry import arg, pipeline
from noetic.orchestration.run import PipelineError
from noetic.orchestration.steps import agent_step
from noetic.tools import prompts


@pipeline("replicate", kind="code", help="reference sites → build brief (→ code with --build)", args=[
  arg("frameworks", nargs="+", help="one or more framework slugs"),
  arg("urls", nargs="+", help="reference URLs (awwwards, dribbble, portfolios…)"),
  arg("--framework", help="legacy single framework slug (backward compatibility)"),
  arg("--goal", default="", help="what you want to build"),
  arg("--build", help="path to a git repo: an agent implements the brief on a new branch (never commits)"),
  arg("--build-agent", help="force the build agent (default: config steps.build, then the ordered agents list)"),
  arg("--allow-order-precedence", action="store_true", help="resolve same-tier collisions using argument order"),
  arg("--max-tokens", type=int, default=4000, help="maximum tokens for stacked heuristics bundle"),
])
def replicate(run, a):
  cfg = run.cfg
  raw_fw = a.get("frameworks") or a.get("framework")
  if not raw_fw:
    raise PipelineError("FRAMEWORK_NOT_FOUND", "No framework specified")
  slugs = [raw_fw] if isinstance(raw_fw, str) else list(raw_fw)

  # Check existence of every requested framework
  for slug in slugs:
    fw_file = cfg.frameworks / f"{slug}.md"
    if not fw_file.exists():
      close = [p.stem for p in cfg.frameworks.glob("*.md") if slug.split("-")[0] in p.stem]
      raise PipelineError("FRAMEWORK_NOT_FOUND", slug, did_you_mean=close)

  # Synthesize stacked charter using stack_frameworks logic [R1+R2]
  def synthesize():
    charter = stack_frameworks_logic(
        cfg,
        slugs,
        task=a.get("goal") or "UI replication",
        allow_order_precedence=a.get("allow_order_precedence", False),
        max_tokens=a.get("max_tokens", 4000),
        include_unapproved=True,
    )
    if charter.get("error") and not charter.get("schema_version"):
      raise PipelineError(charter.get("error", "STACKING_ERROR"), f"Failed to stack frameworks: {charter.get('error')}")
    return charter

  charter = run.step("stack-frameworks", synthesize)

  # Format harmonized heuristics and active primitives for the deconstruct prompt
  heuristics_lines = []
  for h in charter.get("harmonized_heuristics", []):
    heuristics_lines.append(
        f"- [{h.get('framework_slug')}] In {h['context']}: Prioritize {h['prioritize']} over {h['over']} "
        f"because {h['because']}. (Rule: {h['operational_rule']}) [Tier {h['tier']}]"
    )
  heuristics_text = "\n".join(heuristics_lines) if heuristics_lines else "- _none declared_"

  primitives_lines = []
  for p in charter.get("active_primitives", []):
    primitives_lines.append(f"- {p['name']} ({p['kind']}): {p['definition']}")
  primitives_text = "\n".join(primitives_lines) if primitives_lines else "- _none declared_"

  framework_body = (
      f"### Active Stacked Frameworks: {', '.join(slugs)}\n\n"
      f"#### Active Primitives:\n{primitives_text}\n\n"
      f"#### Harmonized Directional Heuristics:\n{heuristics_text}"
  )

  # The stacked framework instructions guide deconstruction
  prompt = prompts.render(cfg, "deconstruct", {
    "framework": framework_body,
    "references": "\n".join(f"- {u}" for u in a["urls"]),
    "goal": a.get("goal") or "a component/section inspired by these references",
  })
  spec = run.step("deconstruct", lambda: agent_step(run, "deconstruct", "deconstruct", prompt, "ui_spec",
                                                    agent=a.get("agent"), web=True, timeout=1500))

  def write_brief():
    brief = notes.build_brief(
        cfg,
        spec,
        slugs if len(slugs) > 1 else slugs[0],
        run.agent_for("deconstruct"),
        run.id,
        charter=charter,
    )
    for s in slugs:
      fw_p = cfg.frameworks / f"{s}.md"
      if fw_p.exists():
        notes.append_application(fw_p, "code", brief)
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
