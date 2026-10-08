"""Tools layer: tool registry.

Every worker tool is registered with @tool and stored in TOOLS.
Core tools are declared in noetic.tools.builtin; workflow tools
are registered by their workflow modules at import time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

TOOLS: dict[str, Tool] = {}


@dataclass(frozen=True)
class Tool:
  name: str
  fn: Callable
  help: str
  needs_cfg: bool = False


def tool(name: str, *, help: str, needs_cfg: bool = False):
  """Decorator registering a tool in TOOLS."""
  def deco(fn: Callable) -> Callable:
    TOOLS[name] = Tool(name=name, fn=fn, help=help, needs_cfg=needs_cfg)
    return fn
  return deco


def call(name: str, cfg: Any = None, **kwargs) -> Any:
  """Call a registered tool by name."""
  if name not in TOOLS:
    raise KeyError(f"unknown tool '{name}'")
  t = TOOLS[name]
  if t.needs_cfg:
    if cfg is None:
      raise ValueError(f"tool '{name}' requires cfg")
    return t.fn(cfg, **kwargs)
  return t.fn(**kwargs)


def discover() -> dict[str, Tool]:
  """Import builtin tools, then trigger workflow discovery so all tools register."""
  import noetic.tools.builtin  # noqa: F401
  from noetic.orchestration import registry as orch_registry
  orch_registry.discover()
  return TOOLS
