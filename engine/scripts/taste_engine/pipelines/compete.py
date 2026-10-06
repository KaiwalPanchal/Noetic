"""compete: competitor intelligence & market exploration → research note + signals."""

from __future__ import annotations

from pathlib import Path

from taste_engine.knowledge import context, notes
from taste_engine.orchestration.registry import arg, pipeline
from taste_engine.orchestration.steps import agent_step
from taste_engine.tools import prompts
from taste_engine.tools.links import url_ok


def dead_links(d: dict) -> list[str]:
  problems = []
  for c in d.get("competitors", []):
    if c.get("url") and not url_ok(c["url"]):
      problems.append(f"competitor URL does not resolve (404/unreachable): {c['url']}")
  for s in d.get("signals_kept", []):
    if s.get("url") and not url_ok(s["url"]):
      problems.append(f"kept signal URL does not resolve (404/unreachable): {s['url']}")
  return problems


@pipeline("compete", kind="project", help="competitor & market intelligence research",
          args=[arg("target", help="idea slug or target market topic")])
def compete(run, a):
  cfg, target = run.cfg, a["target"]

  # Load existing idea context if it exists in the vault
  idea_context = ""
  idea_file = cfg.vault / "ideas" / target / "idea.md"
  if idea_file.exists():
    idea_context = f"\n\nExisting Idea Note ({idea_file.name}):\n" + idea_file.read_text(encoding="utf-8")[:4000]

  vault_notes = context.search(cfg, target.replace("-", " ").split(), limit=6)
  context_str = (vault_notes + idea_context).strip()

  prompt = prompts.render(cfg, "compete", {"target": target, "vault_notes": context_str})
  data = run.step("compete_research", lambda: agent_step(
    run, "compete_research", "research", prompt, "compete",
    agent=a.get("agent"), web=True, timeout=1800, extra_check=dead_links
  ))

  def write():
    agent = run.agent_for("compete_research")
    outputs = []

    # 1. Write the competitor research note
    res_path = notes.competitor_research(cfg, data, agent, run.id)
    outputs.append(res_path)

    # 2. Write signal notes for kept signals
    for s in data.get("signals_kept", []):
      signal_dict = {
        "title": s["title"],
        "url": s["url"],
        "kind": s.get("kind") if s.get("kind") in ("paper", "repo", "postmortem", "web") else "web",
        "mechanism": s.get("mechanism", []),
        "signal_to_noise": s.get("signal_to_noise", "high"),
        "genealogy": f"Competitor intelligence research for {target}",
        "interest": "market-intelligence",
        "tweet_angle": s.get("takeaway", ""),
      }
      outputs.append(notes.signal(cfg, signal_dict, agent, run.id))

    return [run.output(p) for p in outputs]

  return run.step("write", write)
