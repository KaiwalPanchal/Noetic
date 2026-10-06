"""Run state, the pipeline registry, the agent step (retry/fallback) and the human gate."""

import json

import pytest

from taste_engine.actions import gate
from taste_engine.knowledge import notes
from taste_engine.orchestration import registry
from taste_engine.orchestration import steps as steps_mod
from taste_engine.orchestration.cli import attach_agent_notes, show_status
from taste_engine.orchestration.run import PipelineError, Run
from taste_engine.tools.agents import AgentResult

from .conftest import sample_curation


# -- registry -----------------------------------------------------------------

def test_pipeline_decorator_registers_and_validates_kind():
  @registry.pipeline("zz-test", kind="knowledge", help="h", args=[registry.arg("x")])
  def fn(run, a):
    return []
  try:
    p = registry.PIPELINES["zz-test"]
    assert p.fn is fn and p.kind == "knowledge" and p.args == [(("x",), {})]
  finally:
    registry.PIPELINES.pop("zz-test", None)
  with pytest.raises(ValueError):
    registry.pipeline("bad", kind="nonsense", help="")


def test_discover_loads_all_builtin_pipelines():
  found = registry.discover()
  assert {"ingest", "curate", "research", "replicate"} <= set(found)
  assert all(p.kind in registry.KINDS for p in found.values())


# -- Run ----------------------------------------------------------------------

def test_run_persists_state_and_caches_finished_steps(cfg):
  run = Run(cfg, "ingest", {"source": "My Book"})
  assert run.path.is_file() and "my-book" in run.id
  calls = []

  def work():
    calls.append(1)
    return {"v": 1}
  assert run.step("a", work) == {"v": 1}
  assert run.step("a", work) == {"v": 1}  # cached in the same run
  assert calls == [1]

  resumed = Run(cfg, "ingest", {}, run_id=run.id)  # a fresh process resuming
  assert resumed.step("a", work) == {"v": 1}
  assert calls == [1]


def test_failed_step_marks_run_failed_and_resume_continues_from_it(cfg):
  run = Run(cfg, "curate", {"focus": "x"})
  run.step("one", lambda: "ok1")

  def bad():
    raise PipelineError("BOOM", "it broke")
  with pytest.raises(PipelineError):
    run.step("two", bad)
  state = json.loads(run.path.read_text(encoding="utf-8"))
  assert state["status"] == "failed" and state["error"]["code"] == "BOOM"
  assert state["steps"]["one"]["status"] == "done" and state["steps"]["two"]["status"] == "failed"

  resumed = Run(cfg, "curate", {}, run_id=run.id)
  assert resumed.state["status"] == "running"
  assert resumed.step("one", lambda: pytest.fail("must not rerun")) == "ok1"
  assert resumed.step("two", lambda: "ok2") == "ok2"


def test_run_output_is_vault_relative_and_deduped(cfg):
  run = Run(cfg, "x", {})
  p = cfg.vault / "frameworks" / "a.md"
  assert run.output(p) == "frameworks\\a.md" or run.output(p) == "frameworks/a.md"
  run.output(p)
  assert len(run.state["outputs"]) == 1
  assert run.output(cfg.vault.parent / "elsewhere.md").endswith("elsewhere.md")


def test_run_collects_harness_notes_and_finishes(cfg):
  run = Run(cfg, "x", {})
  run.add_notes("s", "claude", ["could not verify X"])
  assert run.notes == ["[s · claude] could not verify X"]
  run.set_agent("s", "claude")
  assert run.agent_for("s") == "claude" and run.agent_for("missing") == "agent"
  run.finish()
  assert json.loads(run.path.read_text(encoding="utf-8"))["status"] == "pending_review"


def test_pipeline_error_payload_is_compact_json():
  err = PipelineError("CODE", "d" * 1000, agent="claude")
  assert err.payload["code"] == "CODE" and len(err.payload["detail"]) == 300
  assert json.loads(str(err))["agent"] == "claude"


# -- agent_step ---------------------------------------------------------------

def scripted(monkeypatch, results):
  """Replace run_agent with a script of AgentResults; records (agent, prompt)."""
  calls = []
  queue = list(results)

  def fake(agent, prompt, schema, **kw):
    calls.append((agent, prompt, kw))
    res = queue.pop(0)
    res.agent = agent
    return res
  monkeypatch.setattr(steps_mod, "run_agent", fake)
  return calls


def ok(data):
  return AgentResult("x", True, data=data, seconds=0.1)


def fail(code, detail="d"):
  return AgentResult("x", False, error={"status": "error", "agent": "x", "code": code, "detail": detail})


def test_agent_step_returns_validated_output_and_records_agent(cfg, monkeypatch):
  calls = scripted(monkeypatch, [ok(sample_curation())])
  run = Run(cfg, "curate", {})
  data = steps_mod.agent_step(run, "select", "curate", "PROMPT", "curation")
  assert data["packages"]
  assert calls[0][0] == "claude" and run.agent_for("select") == "claude"
  assert run.state["steps"]["select"]["attempts"][0]["validated"] is True


def test_agent_step_retries_same_agent_with_exact_schema_errors(cfg, monkeypatch):
  bad = sample_curation()
  del bad["rejected"]
  calls = scripted(monkeypatch, [ok(bad), ok(sample_curation())])
  run = Run(cfg, "curate", {})
  steps_mod.agent_step(run, "select", "curate", "PROMPT", "curation")
  assert [c[0] for c in calls] == ["claude", "claude"]
  assert "missing 'rejected'" in calls[1][1]
  assert calls[1][1].startswith("PROMPT")


def test_agent_step_falls_back_on_infra_failure(cfg, monkeypatch):
  calls = scripted(monkeypatch, [fail("QUOTA_EXCEEDED"), ok(sample_curation())])
  run = Run(cfg, "curate", {})
  steps_mod.agent_step(run, "select", "curate", "P", "curation")
  assert [c[0] for c in calls] == ["claude", "agy"]  # fallback list skips the one already tried
  assert run.agent_for("select") == "agy"


def test_agent_step_forced_agent_disables_fallback(cfg, monkeypatch):
  scripted(monkeypatch, [fail("CLI_NOT_FOUND")])
  run = Run(cfg, "curate", {})
  with pytest.raises(PipelineError) as exc:
    steps_mod.agent_step(run, "select", "curate", "P", "curation", agent="codex")
  assert exc.value.payload["code"] == "CLI_NOT_FOUND"


def test_agent_step_raises_when_every_agent_fails(cfg, monkeypatch):
  scripted(monkeypatch, [fail("TIMEOUT"), fail("TIMEOUT"), fail("TIMEOUT")])
  with pytest.raises(PipelineError) as exc:
    steps_mod.agent_step(Run(cfg, "c", {}), "s", "curate", "P", "curation")
  assert exc.value.payload["code"] == "TIMEOUT"


def test_agent_step_retries_non_infra_failure_once_then_moves_on(cfg, monkeypatch):
  calls = scripted(monkeypatch, [fail("NO_STRUCTURED_OUTPUT"), ok(sample_curation())])
  steps_mod.agent_step(Run(cfg, "c", {}), "s", "curate", "P", "curation")
  assert [c[0] for c in calls] == ["claude", "claude"]
  assert "no usable JSON" in calls[1][1]


def test_agent_step_write_mode_never_blind_retries(cfg, monkeypatch):
  calls = scripted(monkeypatch, [fail("NO_STRUCTURED_OUTPUT"), ok(sample_curation())])
  run = Run(cfg, "c", {})
  steps_mod.agent_step(run, "s", "curate", "P", "curation", write=True)
  assert [c[0] for c in calls] == ["claude", "agy"]  # went to the next agent, not a same-agent retry


def test_agent_step_extra_check_problems_trigger_retry(cfg, monkeypatch):
  calls = scripted(monkeypatch, [ok(sample_curation()), ok(sample_curation())])
  seen = iter([["custom problem"], []])
  steps_mod.agent_step(Run(cfg, "c", {}), "s", "curate", "P", "curation", extra_check=lambda d: next(seen))
  assert len(calls) == 2 and "custom problem" in calls[1][1]


def test_agent_step_logs_agent_reported_gaps(cfg, monkeypatch):
  data = sample_curation()
  data["harness_notes"] = ["assumed UTC"]
  scripted(monkeypatch, [ok(data)])
  run = Run(cfg, "c", {})
  steps_mod.agent_step(run, "s", "curate", "P", "curation")
  assert any("assumed UTC" in n for n in run.notes)


# -- human gate ---------------------------------------------------------------

def make_note(cfg, name="n.md"):
  path = cfg.vault / name
  path.write_text(notes.frontmatter(cfg, "claude", "run-1", "curation") + "# Body\n", encoding="utf-8")
  return path


def test_gate_flow_approve_reject_and_require(cfg):
  path = make_note(cfg)
  assert gate.status_of(path) == "pending_review"
  with pytest.raises(gate.GateClosed):
    gate.require_approved(path)
  gate.approve(path, "looks good")
  assert gate.status_of(path) == "approved"
  gate.require_approved(path)  # no raise
  text = path.read_text(encoding="utf-8")
  assert 'review_note: "looks good"' in text and "# Body" in text
  gate.reject(path, "nope")
  assert gate.status_of(path) == "rejected"
  with pytest.raises(gate.GateClosed):
    gate.require_approved(path)


def test_set_status_rejects_unknown_status_and_missing_frontmatter(cfg):
  path = make_note(cfg)
  with pytest.raises(ValueError):
    notes.set_status(path, "published-ish")
  plain = cfg.vault / "plain.md"
  plain.write_text("no frontmatter", encoding="utf-8")
  with pytest.raises(ValueError):
    notes.set_status(plain, "approved")


# -- cli helpers --------------------------------------------------------------

def test_attach_agent_notes_is_idempotent_and_skips_non_markdown(cfg):
  path = make_note(cfg)
  other = cfg.vault / "data.json"
  other.write_text("{}", encoding="utf-8")
  attach_agent_notes(cfg, ["n.md", "data.json", "missing.md"], ["flagged thing"])
  attach_agent_notes(cfg, ["n.md"], ["flagged thing"])
  text = path.read_text(encoding="utf-8")
  assert text.count("Agent notes") == 1 and "- flagged thing" in text
  assert other.read_text(encoding="utf-8") == "{}"


def test_show_status_lists_and_inspects_runs(cfg, capsys):
  show_status(cfg, None)
  assert "No runs yet" in capsys.readouterr().out
  run = Run(cfg, "curate", {"focus": "f"})
  run.step("gather", lambda: "x")
  show_status(cfg, None)
  assert run.id in capsys.readouterr().out
  show_status(cfg, run.id)
  assert json.loads(capsys.readouterr().out)["id"] == run.id
