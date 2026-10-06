"""Briefing: deterministic JSON first; narration through the neutral runner lands pending_review."""

from datetime import date
import json

import pytest
from typer.testing import CliRunner

from taste_engine.actions import gate
from taste_engine.cli import app
from taste_engine.orchestration import registry as pipe_registry
from taste_engine.orchestration import steps as steps_mod
from taste_engine.orchestration.run import PipelineError, Run
from taste_engine.pipelines import briefing
from taste_engine.tools import agents, prompts
from taste_engine.tools.agents import AgentResult
from taste_engine.tools.schema_check import check

from .conftest import TODAY

D = date.fromisoformat(TODAY)
runner = CliRunner()

NARRATIVE = {
    "headline": "Ship Alpha; Delta is blocked.",
    "next_actions": [{"project": "Alpha", "action": "Ship the thing", "blocked_by": "needs review before release"}],
    "gate_violations": [], "stale_flags": ["Alpha: 36 days"], "check_in": ["What moved on Alpha?"],
    "harness_notes": [],
}


def test_briefing_json_matches_schema_and_content(ocfg):
  b = briefing.build_briefing(ocfg, today=D)
  assert check(b, prompts.schema("briefing")) == []
  assert b["generated"] == TODAY
  assert {p["name"] for p in b["projects"]} == {"Alpha", "Beta", "Gamma", "Delta"}
  assert [s["name"] for s in b["stale"]] == ["Alpha"]  # parked Beta is not stale; Gamma has no date
  gates = {g["project"]: g["gate"] for g in b["gates"]}
  assert gates["Alpha"] == "needs review before release" and "Delta" in gates  # blocked, no gate recorded
  assert {q["id"]: q["overdue"] for q in b["quests"]}["QUEST-001"] is True
  assert b["log_tail"][-1] == "entry 29"
  assert b["focus"]["kind"] == "quest" and b["focus"]["name"] == "QUEST-001"
  assert "SECRET-PROFILE-TOKEN" not in json.dumps(b)


def test_focus_falls_back_to_stalest_active_project(ocfg):
  (ocfg.overmind / "wiki" / "quests" / "QUEST-001-ship.md").unlink()
  b = briefing.build_briefing(ocfg, today=D)
  assert b["focus"]["kind"] == "project" and b["focus"]["name"] == "Alpha"


def test_briefing_without_overmind_is_empty_with_warning(cfg):
  b = briefing.build_briefing(cfg, today=D)
  assert b["projects"] == [] and b["focus"] is None and b["warnings"]
  assert check(b, prompts.schema("briefing")) == []


def _env(monkeypatch, vault):
  monkeypatch.setenv("TASTE_ENGINE_VAULT", str(vault))
  monkeypatch.chdir(vault)


def test_cli_briefing_json_needs_no_agent_cli(ovault, monkeypatch):
  _env(monkeypatch, ovault)
  monkeypatch.setattr(agents.shutil, "which", lambda n: None)  # zero CLIs installed
  res = runner.invoke(app, ["briefing", "--json"])
  assert res.exit_code == 0, res.output
  assert {p["name"] for p in json.loads(res.output)["projects"]} == {"Alpha", "Beta", "Gamma", "Delta"}


def test_cli_briefing_text_and_projects(ovault, monkeypatch):
  _env(monkeypatch, ovault)
  res = runner.invoke(app, ["briefing"])
  assert res.exit_code == 0 and "Alpha" in res.output and "QUEST-001" in res.output
  res = runner.invoke(app, ["projects"])
  assert res.exit_code == 0 and "Gamma" in res.output and "incomplete" in res.output.lower()
  assert len(json.loads(runner.invoke(app, ["projects", "--json"]).output)) == 4


def test_cli_agent_flag_requires_narrate(ovault, monkeypatch):
  _env(monkeypatch, ovault)
  assert runner.invoke(app, ["briefing", "--agent", "codex"]).exit_code != 0


def test_briefing_pipeline_registered():
  assert "briefing" in pipe_registry.discover()


def test_narrate_lands_pending_review_note_via_neutral_runner(ocfg, monkeypatch):
  seen = []

  def fake(agent, prompt, schema, **kw):
    seen.append((agent, prompt))
    return AgentResult(agent, True, data=NARRATIVE, seconds=0.1)
  monkeypatch.setattr(steps_mod, "run_agent", fake)
  out = briefing.briefing(Run(ocfg, "briefing", {}), {})
  note = ocfg.vault / out[0]
  assert gate.status_of(note) == "pending_review"
  assert "Ship Alpha" in note.read_text(encoding="utf-8")
  agent, prompt = seen[0]
  assert agent == "claude"  # first in the configured order; nothing hardcoded
  assert "QUEST-001" in prompt and "SECRET-PROFILE-TOKEN" not in prompt
  assert "pending_review" in prompt  # the overmind.md contract was included


def test_narrate_persona_optional_and_profile_blocked(ocfg, monkeypatch):
  seen = []

  def fake(agent, prompt, schema, **kw):
    seen.append(prompt)
    return AgentResult(agent, True, data=NARRATIVE)
  monkeypatch.setattr(steps_mod, "run_agent", fake)
  persona = ocfg.vault / "persona.md"
  persona.write_text("Speak like a drill sergeant.", encoding="utf-8")
  ocfg.persona = persona
  briefing.briefing(Run(ocfg, "briefing", {}), {})
  assert "drill sergeant" in seen[-1]

  ocfg.persona = ocfg.overmind / "wiki" / "profile" / "secret.md"
  with pytest.raises(PipelineError) as exc:
    briefing.briefing(Run(ocfg, "briefing", {}), {})
  assert exc.value.payload["code"] == "PERSONA_BLOCKED"


def test_cli_narrate_end_to_end(ovault, monkeypatch):
  _env(monkeypatch, ovault)
  monkeypatch.setattr(steps_mod, "run_agent", lambda agent, prompt, schema, **kw: AgentResult(agent, True, data=NARRATIVE))
  res = runner.invoke(app, ["briefing", "--narrate", "--agent", "codex"])
  assert res.exit_code == 0, res.output
  assert "pending_review" in res.output
