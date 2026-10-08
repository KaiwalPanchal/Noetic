"""research: web → taste-filtered signals + one curation package. Links are verified in code."""

from overmind.knowledge import context, notes
from overmind.orchestration.registry import arg, pipeline
from overmind.orchestration.steps import agent_step
from overmind.tools import prompts
from overmind.tools.links import url_ok


def dead_links(d: dict) -> list[str]:
  return [f"kept source URL does not resolve (404/unreachable), so replace or drop it: {s['url']}"
          for s in d["kept"] if not url_ok(s["url"])]


@pipeline("research", kind="content", help="web research → signals + curation package",
          args=[arg("topic")])
def research(run, a):
  cfg, topic = run.cfg, a["topic"]
  prompt = prompts.render(cfg, "research", {"topic": topic, "vault_notes": context.search(cfg, topic.split(), limit=6)})
  data = run.step("research", lambda: agent_step(run, "research", "research", prompt, "research",
                                                  agent=a.get("agent"), web=True, timeout=1500, extra_check=dead_links))

  def write():
    agent = run.agent_for("research")
    for r in data["rejected"]:
      if r["url"] and not url_ok(r["url"]):
        r["reason"] = f"{r['reason']} _(URL unverified: did not resolve)_"
    paths = [notes.signal(cfg, s, agent, run.id) for s in data["kept"]]
    pkg = notes.curation_package(cfg, data["package"], agent, run.id)
    extra = notes.rejected_section(data["rejected"], key="title")
    if data["contradictions"]:
      extra += "\n## ⚠️ Challenges to existing stances\n" + notes.bullets(data["contradictions"]) + "\n"
    pkg.write_text(pkg.read_text(encoding="utf-8") + extra, encoding="utf-8")
    return [run.output(p) for p in paths + [pkg]]
  return run.step("write", write)
