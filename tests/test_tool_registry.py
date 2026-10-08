"""Tests for noetic.tools.registry."""

from __future__ import annotations

import pytest

from noetic.tools import registry


def test_register_and_call():
  @registry.tool("custom_test_tool", help="a test tool")
  def dummy(x: int) -> int:
    return x * 2

  assert registry.call("custom_test_tool", x=5) == 10


def test_unknown_tool_raises_key_error():
  with pytest.raises(KeyError) as exc:
    registry.call("non_existent_tool_12345")
  assert "unknown tool" in str(exc.value)


def test_needs_cfg_without_cfg_raises_value_error():
  @registry.tool("cfg_dependent_tool", help="needs cfg", needs_cfg=True)
  def with_cfg(cfg, msg: str = ""):
    return f"{cfg.owner}:{msg}"

  with pytest.raises(ValueError) as exc:
    registry.call("cfg_dependent_tool", msg="hello")
  assert "requires cfg" in str(exc.value)


def test_discover_contains_builtins_and_workflow_tools():
  tools = registry.discover()
  expected = {
    "clip_url",
    "verify_url",
    "check_schema",
    "tweet_length",
    "focus_get",
    "park_idea",
    "scan_inbox",
  }
  for name in expected:
    assert name in tools, f"tool '{name}' missing from discover()"
