"""Orchestration layer: the pipeline registry.

A pipeline is a function `fn(run, args) -> list[str]` (the output paths),
registered with @pipeline. Drop a new module into taste_engine/pipelines/ and
it shows up in the CLI automatically.

  from taste_engine.orchestration.registry import arg, pipeline

  @pipeline("index", kind="knowledge", help="rebuild the vault index",
            args=[arg("--full", action="store_true")])
  def index(run, a):
      ...
      return [run.output(path)]
"""

from __future__ import annotations

from dataclasses import dataclass, field
import importlib
import pkgutil
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
  """Import every module in taste_engine.pipelines so their decorators run."""
  import taste_engine.pipelines as pkg
  for mod in pkgutil.iter_modules(pkg.__path__):
    if not mod.name.startswith("_"):
      importlib.import_module(f"{pkg.__name__}.{mod.name}")
  return PIPELINES
