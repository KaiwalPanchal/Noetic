"""Tests for noetic.gates.taste (deterministic taste gate)."""

from __future__ import annotations

from pathlib import Path
import pytest

from noetic.agents.runners import AgentResult
from noetic.gates import taste
from noetic.orchestration import steps as steps_mod
from noetic.orchestration.run import Run
from .conftest import sample_curation


def test_no_files_load_returns_none(cfg):
  rules = taste.load(cfg)
  assert rules is None


def test_parse_all_sections_and_dogmas(cfg):
  taste_dir = cfg.state_dir / "taste"
  taste_dir.mkdir(parents=True, exist_ok=True)
  (taste_dir / "dogmas.md").write_text("Subtraction over addition. Calm execution.", encoding="utf-8")
  (taste_dir / "anti-patterns.md").write_text("""
## Banned phrases
- delve into
- game-changer

## Banned patterns
- `\\bgame[- ]changer\\b`
- `\\bdeep[- ]dive\\b`

## Required
- concrete mechanism
""", encoding="utf-8")

  rules = taste.load(cfg)
  assert rules is not None
  assert rules.dogmas == "Subtraction over addition. Calm execution."
  assert rules.phrases == ["delve into", "game-changer"]
  assert len(rules.patterns) == 2
  assert rules.required == ["concrete mechanism"]


def test_phrase_hit_and_miss_case_insensitive(cfg):
  rules = taste.TasteRules(
    dogmas="",
    phrases=["Delve Into"],
    patterns=[],
    required=[],
  )
  # Hit
  v_hit = taste.violations(rules, {"title": "Let us delve into this topic"})
  assert len(v_hit) == 1
  assert 'banned phrase "Delve Into"' in v_hit[0]

  # Miss
  v_miss = taste.violations(rules, {"title": "A direct analysis of this topic"})
  assert v_miss == []


def test_regex_hit(cfg):
  rules = taste.TasteRules(
    dogmas="",
    phrases=[],
    patterns=[taste.re.compile(r"\bgame[- ]changer\b", taste.re.IGNORECASE)],
    required=[],
  )
  v = taste.violations(rules, {"summary": "This tool is a game changer for devs"})
  assert len(v) == 1
  assert 'banned pattern "\\bgame[- ]changer\\b"' in v[0]


def test_required_missing(cfg):
  rules = taste.TasteRules(
    dogmas="",
    phrases=[],
    patterns=[],
    required=["mechanism"],
  )
  # Missing
  v_missing = taste.violations(rules, {"summary": "A high level overview without specifics"})
  assert any('missing required text "mechanism"' in m for m in v_missing)

  # Present
  v_present = taste.violations(rules, {"summary": "Explains the underlying mechanism clearly"})
  assert not any('missing required text "mechanism"' in m for m in v_present)


def test_nested_path_in_violation_message():
  rules = taste.TasteRules(
    dogmas="",
    phrases=["game changer"],
    patterns=[],
    required=[],
  )
  data = {
    "hooks": [
      {"style": "contrarian", "text": "This is a game changer in computing"},
    ]
  }
  v = taste.violations(rules, data)
  assert len(v) == 1
  assert 'taste: banned phrase "game changer" in $.hooks[0].text' in v[0]


def test_harness_notes_ignored():
  rules = taste.TasteRules(
    dogmas="",
    phrases=["game changer"],
    patterns=[],
    required=[],
  )
  data = {
    "summary": "Clean summary",
    "harness_notes": ["I avoided saying game changer"],
  }
  v = taste.violations(rules, data)
  assert v == []


def test_invalid_regex_raises_value_error(cfg):
  taste_dir = cfg.state_dir / "taste"
  taste_dir.mkdir(parents=True, exist_ok=True)
  (taste_dir / "anti-patterns.md").write_text("""
## Banned patterns
- `[invalid(regex`
""", encoding="utf-8")

  with pytest.raises(ValueError) as exc:
    taste.load(cfg)
  assert "invalid regex" in str(exc.value)


def test_agent_step_taste_integration_retries_on_violation(cfg, monkeypatch):
  taste_dir = cfg.state_dir / "taste"
  taste_dir.mkdir(parents=True, exist_ok=True)
  (taste_dir / "anti-patterns.md").write_text("""
## Banned phrases
- delve into
""", encoding="utf-8")

  calls = []
  curation_bad = sample_curation()
  curation_bad["packages"][0]["thesis"] = "We must delve into caches"

  curation_good = sample_curation()
  curation_good["packages"][0]["thesis"] = "Ownership dictates cache correctness"

  def fake_run_agent(agent, prompt, schema, **kw):
    calls.append(prompt)
    if len(calls) == 1:
      return AgentResult(agent, True, data=curation_bad, seconds=0.1)
    return AgentResult(agent, True, data=curation_good, seconds=0.1)

  monkeypatch.setattr(steps_mod, "run_agent", fake_run_agent)

  run = Run(cfg, "curate", {})
  data = steps_mod.agent_step(run, "select", "curate", "INITIAL_PROMPT", "curation")

  assert len(calls) == 2
  assert "banned phrase" in calls[1]
  assert "delve into" in calls[1]
  assert data["packages"][0]["thesis"] == "Ownership dictates cache correctness"
