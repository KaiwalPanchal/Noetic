"""Orchestration layer: the pipeline registry.

A pipeline is a function `fn(run, args) -> list[str]` (the output paths),
registered with @pipeline. A workflow (workflows/<name>/workflow.py) imports its
pipeline modules from register(app, registry); the loader finds workflows, so the
core never names one.

  from overmind.orchestration.registry import arg, pipeline

  @pipeline("index", kind="knowledge", help="rebuild the vault index",
            args=[arg("--full", action="store_true")])
  def index(run, a):
      ...
      return [run.output(path)]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

KINDS = ("knowledge", "content", "code", "project")


@dataclass
class Pipeline:
  name: str
  fn: Callable
  help: str
  kind: str
  args: list = field(default_factory=list)
  agent_flag: bool = True  # adds --agent to force one agent for the run


PIPELINES: dict[str, Pipeline] = {}


def arg(*flags, **kwargs):
  """Declare a CLI argument for a pipeline (same parameters as argparse.add_argument)."""
  return (flags, kwargs)


def pipeline(name: str, *, help: str, kind: str, args: list | None = None, agent_flag: bool = True):
  if kind not in KINDS:
    raise ValueError(f"pipeline kind must be one of {KINDS}")

  def deco(fn):
    PIPELINES[name] = Pipeline(name, fn, help, kind, list(args or []), agent_flag)
    return fn
  return deco


def discover() -> dict[str, Pipeline]:
  """Load every workflow (workflows/*/workflow.py) so their @pipeline decorators run."""
  from overmind.orchestration import registry as this
  from overmind.orchestration.loader import load_workflows
  load_workflows(None, this)
  return PIPELINES
