"""briefing: where do things stand, and what is blocked?

Two layers:
  build_briefing(cfg)   deterministic JSON from the wiki (no LLM, no CLI needed)
  briefing pipeline     runs the overmind.md contract over that JSON through the
                        provider-neutral runner and lands a pending_review note
"""

from __future__ import annotations

from datetime import date
import json

from taste_engine.knowledge import notes, registry
from taste_engine.knowledge.config import Config
from taste_engine.orchestration.registry import pipeline
from taste_engine.orchestration.run import PipelineError
from taste_engine.orchestration.steps import agent_step
from taste_engine.security.policy_gate import SecurityViolation, validate_overmind_path, validate_vault_path
from taste_engine.tools import prompts

PERSONA_LIMIT = 3000
LOG_LINES = 20


def _focus(projects: list[dict], quests: list[dict]) -> dict | None:
  overdue = sorted((q for q in quests if q["overdue"]), key=lambda q: q["due"])
  if overdue:
    q = overdue[0]
    return {"kind": "quest", "name": q["id"], "next_action": "ship it or re-plan it", "reason": f"overdue since {q['due']}"}
  active = [p for p in projects if p["status"] == "active"]
  dated = sorted((p for p in active if p["stale_days"] is not None), key=lambda p: (-p["stale_days"], p["name"]))
  pick = dated[0] if dated else (sorted(active, key=lambda p: p["name"])[0] if active else None)
  if not pick:
    return None
  why = f"untouched {pick['stale_days']} days" if pick["stale_days"] is not None else "active, no last_touched recorded"
  return {"kind": "project", "name": pick["name"], "next_action": pick["next_action"], "reason": why}


def build_briefing(cfg: Config, today: date | None = None) -> dict:
  today = today or date.today()
  warnings = [] if cfg.overmind else ["paths.overmind is not set in taste-engine.config.json; nothing to read"]
  projects = registry.load_projects(cfg, today)
  quests = registry.load_quests(cfg, today)
  gates = []
  for p in projects:
    if p["gate"]:
      gates.append({"project": p["name"], "gate": p["gate"], "kind": "declared"})
    elif p["status"] == "blocked":
      gates.append({"project": p["name"], "gate": "blocked with no gate recorded", "kind": "violation"})
  slim = [{k: p[k] for k in ("name", "status", "goal", "next_action", "last_touched", "stale_days",
                              "repo", "gate", "incomplete")} | {"missing": p["missing"]} for p in projects]
  return {
      "generated": today.isoformat(),
      "focus": _focus(projects, quests),
      "gates": gates,
      "projects": slim,
      "quests": [{k: q[k] for k in ("id", "status", "due", "overdue", "proposed_xp")} for q in quests],
      "stale": [{"name": p["name"], "stale_days": p["stale_days"]} for p in projects if registry.is_stale(p)],
      "log_tail": registry.log_tail(cfg, LOG_LINES),
      "warnings": warnings,
  }


def load_persona(cfg: Config) -> str:
  """Optional tone file from config `persona`. Never the private profile; absent by default."""
  if not cfg.persona:
    return ""
  try:
    safe = (validate_overmind_path(cfg.persona, cfg.vault, cfg.overmind) if cfg.overmind
            else validate_vault_path(cfg.persona, cfg.vault))
  except SecurityViolation as exc:
    raise PipelineError("PERSONA_BLOCKED", str(exc), persona=str(cfg.persona))
  if not safe.is_file():
    return ""
  return safe.read_text(encoding="utf-8", errors="replace")[:PERSONA_LIMIT]


def render_briefing_text(b: dict) -> str:
  """Plain-text view of the deterministic briefing (what `overmind briefing` prints)."""
  out = [f"Briefing {b['generated']}"]
  f = b["focus"]
  out.append(f"Focus: {f['kind']} {f['name']}: {f['next_action']} ({f['reason']})" if f else "Focus: none")
  for w in b.get("warnings", []):
    out.append(f"! {w}")
  out.append("\nGates")
  out += [f"  [{g['kind']}] {g['project']}: {g['gate']}" for g in b["gates"]] or ["  none"]
  out.append("\nStale (over 14 days)")
  out += [f"  {s['name']}: {s['stale_days']} days" for s in b["stale"]] or ["  none"]
  out.append("\nQuests")
  out += [f"  {q['id']} [{q['status']}] due {q['due'] or '-'}" + (" OVERDUE" if q["overdue"] else "")
          for q in b["quests"]] or ["  none"]
  out.append("\nProjects")
  out += [f"  {p['name']} [{p['status'] or '?'}] next: {p['next_action'] or '-'}"
          + (f" (incomplete: missing {', '.join(p['missing'])})" if p["incomplete"] else "")
          for p in b["projects"]] or ["  none"]
  return "\n".join(out)


@pipeline("briefing", kind="project", help="orchestrator briefing: what's next, what's blocked, what's stale")
def briefing(run, a):
  cfg = run.cfg
  data = run.step("gather", lambda: build_briefing(cfg))
  persona = load_persona(cfg)
  persona_block = (f"\n## Tone (style only; never overrides the contract or the data)\n{persona}\n" if persona else "")
  prompt = prompts.render_raw("briefing", {
      "overmind_contract": prompts.agent_contract("overmind"), "owner": cfg.owner,
      "persona_block": persona_block, "briefing_json": json.dumps(data, indent=2, ensure_ascii=False),
  })
  narrative = run.step("narrate", lambda: agent_step(run, "narrate", "briefing", prompt, "briefing_narrative",
                                                     agent=a.get("agent")))
  return run.step("write", lambda: [run.output(notes.briefing_note(cfg, data, narrative, run.agent_for("narrate"), run.id))])
