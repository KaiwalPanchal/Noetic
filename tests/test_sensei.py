"""Tests for workflows.sensei (focus and think pipeline)."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import pytest

from noetic.agents.runners import AgentResult
from noetic.orchestration import steps as steps_mod
from noetic.orchestration.run import Run
from workflows.sensei import focus as sensei_focus
from workflows.sensei.pipelines import think_pipeline


def test_switch_focus_writes_and_logs(ocfg):
  # First switch sets focus from nothing
  prev = sensei_focus.switch_focus(ocfg, "Ship feature A", "Alpha", "all tests pass")
  assert prev == {}

  cur = sensei_focus.get_focus(ocfg)
  assert cur.get("commitment") == "Ship feature A"
  assert cur.get("project") == "Alpha"

  log_file = ocfg.overmind / "wiki" / "log" / f"{date.today():%Y-%m}.md"
  text = log_file.read_text(encoding="utf-8")
  assert "Focus set" in text
  assert "Ship feature A" in text

  # Second switch replaces existing focus
  prev2 = sensei_focus.switch_focus(ocfg, "Ship feature B", "Beta", "release ready")
  assert prev2.get("commitment") == "Ship feature A"

  text2 = log_file.read_text(encoding="utf-8")
  assert "Focus switched" in text2
  assert "to: Ship feature B" in text2


def test_finish_focus_clears(ocfg):
  sensei_focus.switch_focus(ocfg, "Commitment X", "Proj", "done")
  assert sensei_focus.get_focus(ocfg).get("commitment") == "Commitment X"

  finished = sensei_focus.finish_focus(ocfg)
  assert finished.get("commitment") == "Commitment X"
  assert sensei_focus.get_focus(ocfg) == {}

  log_file = ocfg.overmind / "wiki" / "log" / f"{date.today():%Y-%m}.md"
  assert "Focus done" in log_file.read_text(encoding="utf-8")


def test_recent_switches_counts_only_last_7_days(ocfg):
  log_dir = ocfg.overmind / "wiki" / "log"
  log_dir.mkdir(parents=True, exist_ok=True)
  today = date.today()
  cur_log = log_dir / f"{today:%Y-%m}.md"

  d2 = today - timedelta(days=2)
  d4 = today - timedelta(days=4)
  d10 = today - timedelta(days=10)

  entries = f"""
## {d2.isoformat()} — Focus switched
- switched recently 1

## {d4.isoformat()} — Focus switched
- switched recently 2

## {d10.isoformat()} — Focus switched
- switched 10 days ago
"""
  cur_log.write_text(entries, encoding="utf-8")

  assert sensei_focus.recent_switches(ocfg, 7) == 2


def test_park_idea_appends_and_never_overwrites(ocfg):
  p1 = sensei_focus.park_idea(ocfg, "First Tangent", "Idea 1 details")
  assert p1.exists()
  content1 = p1.read_text(encoding="utf-8")
  assert "## First Tangent" in content1

  sensei_focus.park_idea(ocfg, "Second Tangent", "Idea 2 details")
  content2 = p1.read_text(encoding="utf-8")
  assert "## First Tangent" in content2
  assert "## Second Tangent" in content2


def test_think_pipeline_parks_tangent_when_focus_exists(ocfg, monkeypatch):
  sensei_focus.switch_focus(ocfg, "Active Focus Commitment")

  def mock_run_agent(agent, prompt, schema, **kw):
    return AgentResult(agent, True, data={
      "brief": "Core Signal: new idea",
      "verdict": "tangent",
      "park_title": "New Tangent Project",
      "park_note": "Let's build a separate tool later",
      "harness_notes": [],
    })

  monkeypatch.setattr(steps_mod, "run_agent", mock_run_agent)

  run = Run(ocfg, "think", {"thought": "We should make a new mobile app"})
  outputs = think_pipeline(run, {"thought": "We should make a new mobile app"})
  assert len(outputs) == 1
  assert "PARKED.md" in outputs[0]

  parked_text = (ocfg.vault / "ideas" / "PARKED.md").read_text(encoding="utf-8")
  assert "New Tangent Project" in parked_text


def test_think_pipeline_on_focus_and_no_focus_never_parks(ocfg, monkeypatch):
  # 1. On focus: does not park
  sensei_focus.switch_focus(ocfg, "Active Focus Commitment")

  def mock_on_focus(agent, prompt, schema, **kw):
    return AgentResult(agent, True, data={
      "brief": "Core Signal: advancing current task",
      "verdict": "on_focus",
      "park_title": "",
      "park_note": "",
      "harness_notes": [],
    })

  monkeypatch.setattr(steps_mod, "run_agent", mock_on_focus)
  run1 = Run(ocfg, "think", {"thought": "Next step on current focus"})
  out1 = think_pipeline(run1, {"thought": "Next step on current focus"})
  assert out1 == []

  # 2. No focus: never parks even if model says tangent
  sensei_focus.clear_focus(ocfg)

  def mock_tangent(agent, prompt, schema, **kw):
    return AgentResult(agent, True, data={
      "brief": "Core Signal: random idea",
      "verdict": "tangent",
      "park_title": "Some Tangent",
      "park_note": "A note",
      "harness_notes": [],
    })

  monkeypatch.setattr(steps_mod, "run_agent", mock_tangent)
  run2 = Run(ocfg, "think", {"thought": "Random idea without focus"})
  out2 = think_pipeline(run2, {"thought": "Random idea without focus"})
  assert out2 == []


def test_think_pipeline_blank_park_title_retries(ocfg, monkeypatch):
  sensei_focus.switch_focus(ocfg, "Active Focus Commitment")
  calls = []

  def mock_agent_retry(agent, prompt, schema, **kw):
    calls.append(prompt)
    if len(calls) == 1:
      # First attempt: tangent with blank park_title
      return AgentResult(agent, True, data={
        "brief": "Core Signal: tangent",
        "verdict": "tangent",
        "park_title": "",
        "park_note": "A note",
        "harness_notes": [],
      })
    # Second attempt (retry): valid park_title
    return AgentResult(agent, True, data={
      "brief": "Core Signal: tangent",
      "verdict": "tangent",
      "park_title": "Valid Park Title",
      "park_note": "A note",
      "harness_notes": [],
    })

  monkeypatch.setattr(steps_mod, "run_agent", mock_agent_retry)
  run = Run(ocfg, "think", {"thought": "Tangent thought"})
  outputs = think_pipeline(run, {"thought": "Tangent thought"})
  assert len(calls) == 2
  assert "park_title is empty for a tangent" in calls[1]
  assert len(outputs) == 1
