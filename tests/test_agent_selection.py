"""Config-driven agent selection and the generic command adapter (subprocess mocked)."""

import os
from pathlib import Path
import subprocess

import pytest

from taste_engine.knowledge.config import Config
from taste_engine.orchestration import steps as steps_mod
from taste_engine.orchestration.run import PipelineError, Run
from taste_engine.tools import agents
from taste_engine.tools.agents import AgentResult

from .conftest import sample_curation


def test_agent_order_list_per_step_override_and_dedupe(vault):
  c = Config(vault, {"agents": ["a", "b", "c"], "steps": {"curate": ["c", "x"], "ingest": "b"}})
  assert c.agent_order("research") == ["a", "b", "c"]
  assert c.agent_order("curate") == ["c", "x", "a", "b"]
  assert c.agent_order("ingest") == ["b", "a", "c"]


def test_agent_order_legacy_dict_still_works(vault):
  c = Config(vault, {"agents": {"curate": "codex", "fallback": ["agy"]}})
  assert c.agent_order("curate") == ["codex", "agy"]
  assert c.agent_order("other") == ["agy"]


def test_no_default_agent_anywhere(vault):
  c = Config(vault, {})
  assert c.agent_order("curate") == [] and c.models == {}


def test_no_hardcoded_agent_names_in_orchestration_or_pipelines():
  root = Path(__file__).resolve().parents[1] / "engine" / "scripts" / "taste_engine"
  for d in ("orchestration", "pipelines"):
    for f in (root / d).rglob("*.py"):
      text = f.read_text(encoding="utf-8").lower()
      for name in ("claude", "codex", "gemini", "antigravity", '"agy"'):
        assert name not in text, f"{f.name} mentions {name}"


def test_agent_step_autodetects_installed_when_nothing_configured(vault, monkeypatch):
  cfg = Config(vault, {})
  monkeypatch.setattr(steps_mod, "available", lambda name, commands=None: name == "gemini")
  calls = []

  def fake(agent, prompt, schema, **kw):
    calls.append(agent)
    return AgentResult(agent, True, data=sample_curation())
  monkeypatch.setattr(steps_mod, "run_agent", fake)
  steps_mod.agent_step(Run(cfg, "c", {}), "s", "curate", "P", "curation")
  assert calls == ["gemini"]


def test_agent_step_honest_error_when_no_agent_available(vault, monkeypatch):
  cfg = Config(vault, {})
  monkeypatch.setattr(steps_mod, "available", lambda name, commands=None: False)
  with pytest.raises(PipelineError) as exc:
    steps_mod.agent_step(Run(cfg, "c", {}), "s", "curate", "P", "curation")
  assert exc.value.payload["code"] == "NO_AGENT" and "agents" in exc.value.payload["detail"]


def test_agent_step_passes_command_specs_and_per_step_override(vault, monkeypatch):
  cfg = Config(vault, {"agents": ["a"], "steps": {"curate": "mycli"},
                       "commands": {"mycli": {"argv": ["mycli", "{prompt}"]}}})
  seen = []

  def fake(agent, prompt, schema, **kw):
    seen.append((agent, kw.get("commands")))
    return AgentResult(agent, True, data=sample_curation())
  monkeypatch.setattr(steps_mod, "run_agent", fake)
  steps_mod.agent_step(Run(cfg, "c", {}), "s", "curate", "P", "curation")
  assert seen[0][0] == "mycli" and "mycli" in seen[0][1]


# -- generic command adapter ---------------------------------------------------

def _proc(stdout="", stderr="", code=0):
  return subprocess.CompletedProcess(args=[], returncode=code, stdout=stdout, stderr=stderr)


SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}


@pytest.fixture
def fake_run(monkeypatch):
  calls = []
  monkeypatch.setattr(agents.shutil, "which", lambda n: f"/fake/{n}")

  def install(result):
    def _run(cmd, *, stdin, cwd, timeout):
      calls.append({"cmd": cmd, "stdin": stdin})
      return result
    monkeypatch.setattr(agents, "_run", _run)
    return calls
  return install


def test_command_adapter_inline_prompt_placeholder(fake_run, tmp_path):
  calls = fake_run(_proc(stdout='noise {"ok": true}'))
  specs = {"mycli": {"argv": ["mycli", "--ask", "{prompt}"]}}
  res = agents.run_agent("mycli", "hello", SCHEMA, cwd=tmp_path, commands=specs)
  assert res.ok and res.data == {"ok": True}
  assert calls[0]["cmd"][0] == "/fake/mycli" and "hello" in calls[0]["cmd"][2]
  assert calls[0]["stdin"] is None


def test_command_adapter_prompt_file_placeholder_and_cleanup(tmp_path, monkeypatch):
  seen = {}

  def _run(cmd, *, stdin, cwd, timeout):
    seen["path"] = cmd[-1]
    seen["text"] = open(cmd[-1], encoding="utf-8").read()
    return _proc(stdout='{"ok": true}')
  monkeypatch.setattr(agents.shutil, "which", lambda n: f"/fake/{n}")
  monkeypatch.setattr(agents, "_run", _run)
  res = agents.run_agent("c", "the prompt", SCHEMA, cwd=tmp_path,
                         commands={"c": {"argv": ["c", "run", "{prompt_file}"]}})
  assert res.ok and "the prompt" in seen["text"] and "JSON" in seen["text"]
  assert not os.path.exists(seen["path"])


def test_command_adapter_stdin_when_no_placeholder(fake_run, tmp_path):
  calls = fake_run(_proc(stdout='{"ok": false}'))
  res = agents.run_agent("c", "p", SCHEMA, cwd=tmp_path, commands={"c": {"argv": ["c", "-"]}})
  assert res.ok and "p" in calls[0]["stdin"]


def test_command_adapter_generic_name_and_errors(fake_run, tmp_path):
  spec = {"command": {"argv": ["x", "{prompt}"]}}
  fake_run(_proc(stdout="no json"))
  res = agents.run_agent("command", "p", SCHEMA, cwd=tmp_path, commands=spec)
  assert not res.ok and res.error["code"] == "NO_STRUCTURED_OUTPUT"
  fake_run(_proc(stderr="usage limit reached", code=1))
  res = agents.run_agent("command", "p", SCHEMA, cwd=tmp_path, commands=spec)
  assert res.error["code"] == "QUOTA_EXCEEDED"


def test_command_adapter_missing_cli_unknown_and_bad_spec(monkeypatch, tmp_path):
  monkeypatch.setattr(agents.shutil, "which", lambda n: None)
  res = agents.run_agent("c", "p", SCHEMA, cwd=tmp_path, commands={"c": {"argv": ["nope", "{prompt}"]}})
  assert res.error["code"] == "CLI_NOT_FOUND"
  assert agents.run_agent("zzz", "p", SCHEMA, cwd=tmp_path).error["code"] == "UNKNOWN_AGENT"
  res = agents.run_agent("c", "p", SCHEMA, cwd=tmp_path, commands={"c": {"argv": []}})
  assert res.error["code"] == "BAD_COMMAND_SPEC"


def test_command_adapter_timeout_is_reported(monkeypatch, tmp_path):
  def _run(cmd, *, stdin, cwd, timeout):
    raise subprocess.TimeoutExpired(cmd, timeout)
  monkeypatch.setattr(agents.shutil, "which", lambda n: "/x")
  monkeypatch.setattr(agents, "_run", _run)
  res = agents.run_agent("c", "p", SCHEMA, cwd=tmp_path, timeout=1, commands={"c": {"argv": ["c", "{prompt}"]}})
  assert res.error["code"] == "TIMEOUT"


def test_available_knows_command_specs(monkeypatch):
  monkeypatch.setattr(agents.shutil, "which", lambda n: "/x" if n == "mycli" else None)
  assert agents.available("mycli", {"mycli": {"argv": ["mycli", "{prompt}"]}})
  assert not agents.available("mycli")
