"""curate: vault-only idea mining → 1–3 curation packages (+ what was rejected)."""

import re

from noetic.knowledge import context, notes
from noetic.orchestration.registry import arg, pipeline
from noetic.orchestration.steps import agent_step
from noetic.tools import prompts


@pipeline("curate", kind="content", help="content ideas from your own notes (no web)",
          args=[arg("focus", nargs="?", default="", help="topic to focus on (default: top interests)")])
def curate(run, a):
  cfg = run.cfg
  focus = a.get("focus") or ""
  terms = focus.split() if focus else [w for n in context.interest_names(cfg) for w in re.findall(r"[A-Za-z]{4,}", n)]
  found = run.step("gather", lambda: context.search(cfg, terms))
  prompt = prompts.render(cfg, "curate", {
    "focus": focus or "the owner's highest-weight interests", "archive": context.archive(cfg), "vault_notes": found,
  })
  data = run.step("select", lambda: agent_step(run, "select", "curate", prompt, "curation", agent=a.get("agent")))

  def write():
    agent = run.agent_for("select")
    paths = [notes.curation_package(cfg, p, agent, run.id) for p in data["packages"]]
    if paths and data["rejected"]:
      paths[0].write_text(paths[0].read_text(encoding="utf-8") + notes.rejected_section(data["rejected"]), encoding="utf-8")
    return [run.output(p) for p in paths]
  return run.step("write", write)
