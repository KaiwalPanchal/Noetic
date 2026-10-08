"""Agent CLI adapters, tested with a mocked subprocess. No real CLI is ever called."""

import json
import subprocess
from pathlib import Path

import pytest

from overmind.agents import runners as agents
from overmind.agents.runners import AgentResult, run_agent

SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}


def proc(stdout="", stderr="", code=0):
  return subprocess.CompletedProcess(args=[], returncode=code, stdout=stdout, stderr=stderr)


@pytest.fixture
def fake_cli(monkeypatch):
  """Pretend every agent CLI is installed; capture the command that would run."""
  calls = []
  monkeypatch.setattr(agents.shutil, "which", lambda name: f"/fake/bin/{name}")

  def install(fn):
    def _run(cmd, *, stdin, cwd, timeout):
      calls.append({"cmd": cmd, "stdin": stdin, "cwd": cwd, "timeout": timeout})
      return fn(cmd)
    monkeypatch.setattr(agents, "_run", _run)
    return calls
  return install


# -- helpers ------------------------------------------------------------------

def test_extract_json_handles_fences_and_bare_objects():
  assert agents._extract_json('noise ```json\n{"a": 1}\n``` tail') == {"a": 1}
  assert agents._extract_json('prefix {"a": 2} suffix') == {"a": 2}
  assert agents._extract_json("no json here") is None
  assert agents._extract_json("{broken") is None


def test_strip_for_strict_drops_unsupported_keywords_recursively():
  schema = {"$schema": "x", "title": "t", "type": "object",
            "properties": {"a": {"type": "array", "minItems": 2, "items": {"title": "i", "type": "string"}}}}
  out = agents._strip_for_strict(schema)
  assert "$schema" not in out and "title" not in out
  assert out["properties"]["a"] == {"type": "array", "items": {"type": "string"}}


@pytest.mark.parametrize("stderr,code", [
    ("Error: usage limit reached", "QUOTA_EXCEEDED"),
    ("HTTP 429 too many requests", "QUOTA_EXCEEDED"),
    ("Not logged in. Please authenticate", "AUTH_FAILED"),
    ("segfault", "EXIT_NONZERO"),
])
def test_classify_failure(stderr, code):
  res = agents._classify_failure("claude", proc(stderr=stderr, code=1))
  assert res.ok is False
  assert res.error["code"] == code
  if code == "EXIT_NONZERO":
    assert res.error["exit_code"] == 1


# -- run_agent guard rails ----------------------------------------------------

def test_unknown_agent_is_reported_not_raised(tmp_path):
  res = run_agent("nope", "p", SCHEMA, cwd=tmp_path)
  assert res.error["code"] == "UNKNOWN_AGENT"


def test_missing_cli_reports_cli_not_found_with_fallback_hint(tmp_path, monkeypatch):
  monkeypatch.setattr(agents.shutil, "which", lambda name: None)
  res = run_agent("claude", "p", SCHEMA, cwd=tmp_path)
  assert res.error["code"] == "CLI_NOT_FOUND"
  assert res.error["suggested_fallback"]
  assert agents.available("claude") is False


def test_timeout_is_converted_to_diagnostic(tmp_path, fake_cli):
  def boom(cmd):
    raise subprocess.TimeoutExpired(cmd, 5)
  fake_cli(boom)
  res = run_agent("claude", "p", SCHEMA, cwd=tmp_path, timeout=5)
  assert res.error["code"] == "TIMEOUT"
  assert "5s" in res.error["detail"]


def test_oserror_is_converted_to_cli_not_found(tmp_path, fake_cli):
  def boom(cmd):
    raise OSError("exec format error")
  fake_cli(boom)
  assert run_agent("codex", "p", SCHEMA, cwd=tmp_path).error["code"] == "CLI_NOT_FOUND"


def test_error_detail_is_truncated_and_whitespace_collapsed():
  res = agents._err("x", "C", "a   b\n\n" + "z" * 1000)
  assert len(res.error["detail"]) <= 300
  assert "  " not in res.error["detail"]


# -- claude -------------------------------------------------------------------

def test_claude_success_parses_structured_output_and_cost(tmp_path, fake_cli):
  calls = fake_cli(lambda cmd: proc(json.dumps({"structured_output": {"ok": True}, "total_cost_usd": 0.02})))
  res = run_agent("claude", "do it", SCHEMA, cwd=tmp_path, model="opus")
  assert res.ok and res.data == {"ok": True} and res.cost_usd == 0.02
  cmd = calls[0]["cmd"]
  assert cmd[0] == "/fake/bin/claude"
  assert cmd[cmd.index("--model") + 1] == "opus"
  assert json.loads(cmd[cmd.index("--json-schema") + 1]) == SCHEMA
  assert calls[0]["stdin"] == "do it"
  tools = cmd[cmd.index("--tools") + 1]
  assert "Write" not in tools and "WebFetch" not in tools
  assert "--permission-mode" not in cmd


def test_claude_write_and_web_flags_change_tools_and_permissions(tmp_path, fake_cli):
  calls = fake_cli(lambda cmd: proc(json.dumps({"structured_output": {"ok": True}})))
  run_agent("claude", "p", SCHEMA, cwd=tmp_path, web=True, write=True)
  cmd = calls[0]["cmd"]
  tools = cmd[cmd.index("--tools") + 1].split(",")
  assert {"WebFetch", "WebSearch", "Write", "Edit"} <= set(tools)
  assert cmd[cmd.index("--permission-mode") + 1] == "acceptEdits"


def test_claude_falls_back_to_json_in_result_text(tmp_path, fake_cli):
  fake_cli(lambda cmd: proc(json.dumps({"result": 'here: ```json\n{"ok": false}\n```'})))
  assert run_agent("claude", "p", SCHEMA, cwd=tmp_path).data == {"ok": False}


def test_claude_error_envelope_auth_vs_other(tmp_path, fake_cli):
  fake_cli(lambda cmd: proc(json.dumps({"is_error": True, "result": "Not logged in"}), code=1))
  assert run_agent("claude", "p", SCHEMA, cwd=tmp_path).error["code"] == "AUTH_FAILED"
  fake_cli(lambda cmd: proc(json.dumps({"is_error": True, "result": "kaboom"}), code=1))
  assert run_agent("claude", "p", SCHEMA, cwd=tmp_path).error["code"] == "EXIT_NONZERO"


def test_claude_no_json_anywhere_is_no_structured_output(tmp_path, fake_cli):
  fake_cli(lambda cmd: proc(json.dumps({"result": "I refuse"})))
  assert run_agent("claude", "p", SCHEMA, cwd=tmp_path).error["code"] == "NO_STRUCTURED_OUTPUT"


def test_claude_unparseable_stdout_is_classified_from_stderr(tmp_path, fake_cli):
  fake_cli(lambda cmd: proc("garbage", "rate limit hit", 1))
  assert run_agent("claude", "p", SCHEMA, cwd=tmp_path).error["code"] == "QUOTA_EXCEEDED"


# -- codex --------------------------------------------------------------------

def test_codex_reads_last_message_file_and_uses_strict_schema(tmp_path, fake_cli):
  seen = {}

  def fn(cmd):
    out = Path(cmd[cmd.index("-o") + 1])
    seen["schema"] = json.loads(Path(cmd[cmd.index("--output-schema") + 1]).read_text(encoding="utf-8"))
    out.write_text('{"ok": true}', encoding="utf-8")
    return proc()
  calls = fake_cli(fn)
  schema = {"title": "T", "type": "object", "properties": {"ok": {"type": "boolean"}}}
  res = run_agent("codex", "p", schema, cwd=tmp_path, web=True, write=False, model="gpt-x")
  assert res.ok and res.data == {"ok": True}
  assert "title" not in seen["schema"]
  cmd = calls[0]["cmd"]
  assert "--search" in cmd and cmd[cmd.index("-s") + 1] == "read-only"
  assert cmd[cmd.index("-m") + 1] == "gpt-x"


def test_codex_nonzero_without_output_is_classified(tmp_path, fake_cli):
  fake_cli(lambda cmd: proc("", "401 unauthorized: api key", 1))
  assert run_agent("codex", "p", SCHEMA, cwd=tmp_path).error["code"] == "AUTH_FAILED"


def test_codex_write_uses_workspace_write_sandbox(tmp_path, fake_cli):
  def fn(cmd):
    Path(cmd[cmd.index("-o") + 1]).write_text('{"ok": true}', encoding="utf-8")
    return proc()
  calls = fake_cli(fn)
  run_agent("codex", "p", SCHEMA, cwd=tmp_path, write=True)
  cmd = calls[0]["cmd"]
  assert cmd[cmd.index("-s") + 1] == "workspace-write"


# -- agy ----------------------------------------------------------------------

def test_agy_filters_to_schema_keys_and_cleans_temp_files(tmp_path, fake_cli):
  def fn(cmd):
    return proc(json.dumps({"status": "SUCCESS", "structured_output": {"ok": True, "bookkeeping": 1}}))
  calls = fake_cli(fn)
  res = run_agent("agy", "long prompt", SCHEMA, cwd=tmp_path)
  assert res.data == {"ok": True}
  assert "--mode" in calls[0]["cmd"] and "plan" in calls[0]["cmd"]
  assert calls[0]["stdin"] is None
  assert list((tmp_path / ".taste-engine" / "tmp").iterdir()) == []


def test_agy_write_skips_permissions_and_failure_status_is_reported(tmp_path, fake_cli):
  calls = fake_cli(lambda cmd: proc(json.dumps({"status": "ERROR", "error": "please authenticate"})))
  res = run_agent("agy", "p", SCHEMA, cwd=tmp_path, write=True)
  assert "--dangerously-skip-permissions" in calls[0]["cmd"]
  assert res.error["code"] == "AUTH_FAILED"


def test_agy_prompt_goes_through_file_not_command_line(tmp_path, fake_cli):
  captured = {}

  def fn(cmd):
    short = cmd[cmd.index("-p") + 1]
    path = short.split("Read the file ")[1].split(" in full")[0]
    captured["prompt"] = Path(path).read_text(encoding="utf-8")
    return proc(json.dumps({"status": "SUCCESS", "structured_output": {"ok": True}}))
  fake_cli(fn)
  run_agent("agy", "SECRET-BIG-PROMPT" * 10, SCHEMA, cwd=tmp_path)
  assert captured["prompt"].startswith("SECRET-BIG-PROMPT")


# -- gemini -------------------------------------------------------------------

def test_gemini_embeds_schema_in_prompt_and_tolerates_banner_noise(tmp_path, fake_cli):
  calls = fake_cli(lambda cmd: proc("Loaded cached credentials.\n" + json.dumps({"response": '{"ok": true}'})))
  res = run_agent("gemini", "p", SCHEMA, cwd=tmp_path)
  assert res.ok and res.data == {"ok": True}
  assert "JSON Schema" in calls[0]["stdin"]
  assert calls[0]["cmd"][calls[0]["cmd"].index("--approval-mode") + 1] == "plan"


def test_agent_result_dataclass_defaults():
  r = AgentResult("x", True)
  assert r.data is None and r.error is None and r.seconds == 0.0
