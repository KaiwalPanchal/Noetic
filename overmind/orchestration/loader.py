"""Workflow loader: the only place the core learns that workflows exist.

A workflow is a subpackage of `workflows/` with a `workflow.py` that exposes
`register(app, registry)`. The core never imports a workflow by name; it scans the
`workflows` package, imports each `workflow.py`, and calls `register`. Resources
(prompts, schemas, templates, commands) are found by scanning the same folders.

  app       the Typer app (or None when called from the argparse pipeline CLI)
  registry  overmind.orchestration.registry (workflows add pipelines with @pipeline)
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import Iterator

PACKAGE = "workflows"
_LOADED: set[int] = set()


def _package():
  try:
    return importlib.import_module(PACKAGE)
  except ModuleNotFoundError:
    return None


def workflows_dir() -> Path | None:
  """The folder holding the workflow subpackages, or None when no `workflows` package is importable."""
  pkg = _package()
  paths = list(getattr(pkg, "__path__", [])) if pkg else []
  return Path(paths[0]) if paths else None


def workflow_names() -> list[str]:
  pkg = _package()
  if pkg is None:
    return []
  return sorted(m.name for m in pkgutil.iter_modules(pkg.__path__) if m.ispkg and not m.name.startswith("_"))


def workflow_dirs() -> list[Path]:
  base = workflows_dir()
  return [base / n for n in workflow_names()] if base else []


def load_workflows(app=None, registry=None) -> list[str]:
  """Import every workflows/<name>/workflow.py and call its register(app, registry).

  Idempotent per (app, registry) pair: a second call with the same objects is a no-op, so the
  Typer app is not registered twice. Returns the workflow names that registered.
  """
  if registry is None:
    from overmind.orchestration import registry as _registry
    registry = _registry
  key = hash((id(app), id(registry)))
  names: list[str] = []
  for name in workflow_names():
    mod = importlib.import_module(f"{PACKAGE}.{name}.workflow")
    if not hasattr(mod, "register"):
      raise AttributeError(f"{PACKAGE}.{name}.workflow has no register(app, registry)")
    if key not in _LOADED or app is None:
      mod.register(app, registry)
    names.append(name)
  _LOADED.add(key)
  return names


def resource_dirs(kind: str) -> Iterator[Path]:
  """workflows/*/<kind> folders (kind: prompts | schemas | templates | commands)."""
  for d in workflow_dirs():
    if (d / kind).is_dir():
      yield d / kind


def find_resource(kind: str, filename: str) -> Path:
  for d in resource_dirs(kind):
    if (d / filename).is_file():
      return d / filename
  raise FileNotFoundError(f"no {kind}/{filename} in any workflow")
