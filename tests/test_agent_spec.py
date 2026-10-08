"""Tests for noetic.agents.spec."""

from __future__ import annotations

from pathlib import Path
import pytest

from noetic.agents import spec
from noetic.orchestration import registry as orch_registry
from noetic.tools import registry as tool_registry


def test_parse_valid_spec():
  md = """---
name: sample
description: A sample worker
trigger: on-demand
policy: workflow
pipeline: librarian
tools: [scan_inbox]
---
Prompt body here.
"""
  s = spec.parse(md)
  assert s.name == "sample"
  assert s.description == "A sample worker"
  assert s.trigger == "on-demand"
  assert s.policy == "workflow"
  assert s.pipeline == "librarian"
  assert s.tools == ["scan_inbox"]
  assert s.body == "Prompt body here."


def test_validation_fails_on_invalid_policy():
  s = spec.AgentSpec(
    name="test", description="d", trigger="on-demand", policy="invalid_policy",
    pipeline="librarian", tools=[],
  )
  problems = spec.validate(s, tool_names={}, pipeline_names={"librarian"})
  assert any("invalid policy" in p for p in problems)


def test_validation_fails_on_invalid_trigger():
  s = spec.AgentSpec(
    name="test", description="d", trigger="every-midnight", policy="workflow",
    pipeline="librarian", tools=[],
  )
  problems = spec.validate(s, tool_names={}, pipeline_names={"librarian"})
  assert any("invalid trigger" in p for p in problems)


def test_validation_fails_on_hook_without_payload():
  s = spec.AgentSpec(
    name="test", description="d", trigger="hook:on-save", policy="workflow",
    pipeline="librarian", tools=[], payload=None,
  )
  problems = spec.validate(s, tool_names={}, pipeline_names={"librarian"})
  assert any("requires payload" in p for p in problems)


def test_validation_fails_on_unknown_pipeline():
  s = spec.AgentSpec(
    name="test", description="d", trigger="on-demand", policy="workflow",
    pipeline="ghost_pipeline", tools=[],
  )
  problems = spec.validate(s, tool_names={}, pipeline_names={"librarian"})
  assert any("unknown pipeline 'ghost_pipeline'" in p for p in problems)


def test_validation_fails_on_unknown_tool():
  s = spec.AgentSpec(
    name="test", description="d", trigger="on-demand", policy="workflow",
    pipeline="librarian", tools=["nonexistent_tool"],
  )
  problems = spec.validate(s, tool_names={"scan_inbox"}, pipeline_names={"librarian"})
  assert any("unknown tool 'nonexistent_tool'" in p for p in problems)


def test_validation_fails_on_loop_without_budget():
  s = spec.AgentSpec(
    name="test", description="d", trigger="on-demand", policy="loop",
    pipeline="librarian", tools=[], budget={},
  )
  problems = spec.validate(s, tool_names={}, pipeline_names={"librarian"})
  assert any("budget.max_iterations >= 1" in p for p in problems)


def test_load_specs_finds_librarian_worker_sensei():
  specs = spec.load_specs()
  assert "librarian" in specs
  assert "worker" in specs
  assert "sensei" in specs


def test_every_shipped_spec_validates_with_zero_problems():
  tool_registry.discover()
  orch_registry.discover()
  specs = spec.load_specs()
  for name, s in specs.items():
    problems = spec.validate(s)
    assert not problems, f"shipped spec '{name}' had validation problems: {problems}"


def test_duplicate_name_raises_spec_error(tmp_path: Path, monkeypatch):
  d1 = tmp_path / "w1" / "agents"
  d2 = tmp_path / "w2" / "agents"
  d1.mkdir(parents=True)
  d2.mkdir(parents=True)
  (d1 / "agent.md").write_text("---\nname: dup\ntrigger: on-demand\npolicy: workflow\npipeline: p\n---\n", encoding="utf-8")
  (d2 / "agent.md").write_text("---\nname: dup\ntrigger: on-demand\npolicy: workflow\npipeline: p\n---\n", encoding="utf-8")

  monkeypatch.setattr("noetic.orchestration.loader.resource_dirs", lambda kind: [d1, d2])
  with pytest.raises(spec.SpecError) as exc:
    spec.load_specs()
  assert "duplicate agent spec 'dup'" in str(exc.value)
