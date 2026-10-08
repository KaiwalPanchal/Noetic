"""Sensei pipelines: think pipeline (thought -> brief -> optional parking)."""

from __future__ import annotations

import json
from pathlib import Path

from noetic.agents.spec import load_specs
from noetic.orchestration.registry import arg, pipeline
from noetic.orchestration.steps import agent_step
from workflows.sensei.focus import get_focus, park_idea


@pipeline("think", kind="project", help="Sensei: judge a thought against your focus; parks tangents", args=[arg("thought")])
def think_pipeline(run, a) -> list[str]:
  """Judge a thought against active focus and park tangents."""
  thought = str(a.get("thought", "")).strip()
  cfg = run.cfg

  focus = get_focus(cfg) if cfg.overmind else {}
  specs = load_specs()
  spec = specs["sensei"]

  if focus:
    focus_text = f"Project: {focus.get('project', '?')}\nCommitment: {focus.get('commitment', '?')}\nDone when: {focus.get('done_when', '?')}"
  else:
    focus_text = "No focus set"

  prompt = spec.render({
    "focus": focus_text,
    "thought": thought,
    "owner": cfg.owner,
  })

  def _check(data: dict) -> list[str]:
    if data.get("verdict") == "tangent" and not str(data.get("park_title") or "").strip():
      return ["park_title is empty for a tangent"]
    return []

  data = run.step("judge", lambda: agent_step(run, "judge", "think", prompt, "think_verdict", extra_check=_check, taste=False))

  brief = data.get("brief", "")
  if brief:
    print(brief)

  verdict = data.get("verdict")
  if verdict == "tangent" and focus:
    park_title = str(data.get("park_title") or thought[:60]).strip()
    park_note = str(data.get("park_note") or "").strip()
    parked_path = park_idea(cfg, park_title, park_note, thought=thought, focus=focus)
    return [run.output(parked_path)]

  return []
