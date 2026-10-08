"""journey: build-in-public entry with tweet candidates (privacy-filtered)."""

from overmind.knowledge import context, notes
from overmind.orchestration.registry import arg, pipeline
from overmind.orchestration.steps import agent_step
from overmind.tools import prompts
from overmind.tools.tweets import too_long


@pipeline("journey", kind="content", help="build-in-public entry → Twitter/journey/",
          args=[arg("text", nargs="?", default="", help="what happened (default: summarize the recent log)")])
def journey(run, a):
  cfg = run.cfg
  material = a.get("text") or ""
  log = context.recent_log(cfg)
  if log:
    material += f"\n\nRecent Overmind log (filter out anything private):\n{log}"
  previous_files = sorted((cfg.twitter / "journey").glob("*.md"))[-2:]
  previous = "\n\n".join(f"### {f.stem}\n{context.read_body(f, 1200)}" for f in previous_files) or "(first entry)"
  prompt = prompts.render(cfg, "journey", {"material": material or "(no input; summarize the recent log)", "previous": previous})
  data = run.step("write-entry", lambda: agent_step(
    run, "write-entry", "journey", prompt, "journey", agent=a.get("agent"),
    extra_check=lambda d: too_long(d["tweets"], cfg.x_char_limit)))
  return run.step("write", lambda: [run.output(notes.journey(cfg, data, run.agent_for("write-entry"), run.id))])
