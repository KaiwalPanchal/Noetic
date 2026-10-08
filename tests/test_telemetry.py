"""Tests for OpenTelemetry GenAI tracing instrumentation."""

from noetic.telemetry.tracer import trace_agent_call


def test_telemetry_trace_successful_call():
  with trace_agent_call("claude", model="sonnet", prompt_chars=250) as meta:
    meta["completion_chars"] = 120
    meta["cost_usd"] = 0.004

  assert meta["ok"] is True
  assert meta["completion_chars"] == 120
  assert meta["cost_usd"] == 0.004


def test_telemetry_trace_exception_handled():
  try:
    with trace_agent_call("codex", model="gpt-5", prompt_chars=100) as meta:
      raise ValueError("Simulated network timeout")
  except ValueError:
    pass

  assert meta["ok"] is False
  assert "Simulated network timeout" in meta["error"]
