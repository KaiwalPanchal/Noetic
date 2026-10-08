"""Agents layer: unified agent spec.

Every worker agent in Noetic is defined by a single spec (prompt + tools +
trigger + execution policy). Specs live in workflows/<name>/agents/<agent>.md
with YAML frontmatter and markdown body.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml


class SpecError(Exception):
  """Raised when an agent spec is malformed or invalid."""


@dataclass
class AgentSpec:
  name: str
  description: str
  trigger: str
  policy: str
  pipeline: str
  tools: list[str] = field(default_factory=list)
  payload: str | None = None
  budget: dict = field(default_factory=dict)
  prompt_name: str | None = None
  body: str = ""
  path: Path | None = None

  def render(self, values: dict | None = None) -> str:
    """Render the agent's prompt with strict contract and filled placeholders."""
    from noetic.tools import prompts
    from noetic.orchestration.loader import find_resource
    if self.prompt_name:
      template = find_resource("prompts", f"{self.prompt_name}.md").read_text(encoding="utf-8")
    else:
      template = self.body
    return prompts.contract() + "\n" + prompts.fill(template, values or {})


def parse(text: str, path: Path | str | None = None) -> AgentSpec:
  """Parse an agent spec from markdown with YAML frontmatter."""
  path_obj = Path(path) if path else None
  fm: dict[str, Any] = {}
  body = text
  if text.startswith("---"):
    end = text.find("\n---", 3)
    if end != -1:
      raw_fm = text[3:end]
      body = text[end + 4:].lstrip("\r\n")
      try:
        loaded = yaml.safe_load(raw_fm)
        if isinstance(loaded, dict):
          fm = loaded
      except yaml.YAMLError as exc:
        raise SpecError(f"invalid YAML frontmatter: {exc}")

  name = str(fm.get("name") or (path_obj.stem if path_obj else ""))
  desc = str(fm.get("description") or "")
  trigger = str(fm.get("trigger") or "")
  policy = str(fm.get("policy") or "")
  pipeline = str(fm.get("pipeline") or "")
  tools = list(fm.get("tools") or [])
  payload = fm.get("payload")
  budget = fm.get("budget") or {}
  prompt_name = fm.get("prompt")

  return AgentSpec(
    name=name,
    description=desc,
    trigger=trigger,
    policy=policy,
    pipeline=pipeline,
    tools=tools,
    payload=payload,
    budget=budget,
    prompt_name=prompt_name,
    body=body.strip(),
    path=path_obj,
  )


def load_specs() -> dict[str, AgentSpec]:
  """Scan workflow agent directories and load all specs."""
  from noetic.orchestration.loader import resource_dirs
  specs: dict[str, AgentSpec] = {}
  for d in resource_dirs("agents"):
    for p in sorted(d.glob("*.md")):
      spec = parse(p.read_text(encoding="utf-8"), path=p)
      if spec.name in specs:
        raise SpecError(f"duplicate agent spec '{spec.name}' in {p} and {specs[spec.name].path}")
      specs[spec.name] = spec
  return specs


def validate(
    spec: AgentSpec,
    tool_names: Any = None,
    pipeline_names: Any = None,
) -> list[str]:
  """Validate an AgentSpec against rules and registered tools/pipelines."""
  if tool_names is None:
    from noetic.tools.registry import discover as discover_tools
    tool_names = discover_tools()
  if pipeline_names is None:
    from noetic.orchestration.registry import discover as discover_pipelines
    pipeline_names = discover_pipelines()

  problems: list[str] = []

  # 1. Policy validation
  if spec.policy not in ("workflow", "loop"):
    problems.append(f"invalid policy '{spec.policy}' (must be 'workflow' or 'loop')")

  # 2. Trigger validation
  valid_trigger = False
  if spec.trigger == "on-demand":
    valid_trigger = True
  elif spec.trigger.startswith("schedule:"):
    parts = spec.trigger.split(":", 1)
    if len(parts) == 2 and parts[1] in ("daily", "weekly", "hourly"):
      valid_trigger = True
  elif spec.trigger.startswith("hook:"):
    valid_trigger = True
    if not spec.payload:
      problems.append(f"hook trigger '{spec.trigger}' requires payload")

  if not valid_trigger:
    problems.append(f"invalid trigger '{spec.trigger}'")

  # 3. Pipeline validation
  if spec.pipeline not in pipeline_names:
    problems.append(f"unknown pipeline '{spec.pipeline}'")

  # 4. Tools validation
  for t in spec.tools:
    if t not in tool_names:
      problems.append(f"unknown tool '{t}'")

  # 5. Loop policy budget
  if spec.policy == "loop":
    max_it = spec.budget.get("max_iterations") if isinstance(spec.budget, dict) else None
    if not isinstance(max_it, int) or max_it < 1:
      problems.append("loop policy requires budget.max_iterations >= 1")

  return problems


def find_by_hook(specs: dict[str, AgentSpec] | list[AgentSpec], event: str) -> list[AgentSpec]:
  """Find all specs triggered by a hook event."""
  spec_list = specs.values() if isinstance(specs, dict) else specs
  target = f"hook:{event}"
  return [s for s in spec_list if s.trigger == target]


def run_agent_spec(cfg: Any, name: str, args: dict | None = None) -> Any:
  """Run an agent spec by name."""
  from noetic.orchestration import cli as orch_cli
  specs = load_specs()
  if name not in specs:
    raise KeyError(f"unknown agent '{name}'")
  spec = specs[name]
  return orch_cli.execute(cfg, spec.pipeline, args or {})


def fire_hook(cfg: Any, event: str, text: str = "") -> list[Any]:
  """Fire hook for matching specs and execute them."""
  from noetic.orchestration import cli as orch_cli
  specs = load_specs()
  matched = find_by_hook(specs, event)
  results = []
  for s in matched:
    args_dict = {s.payload: text} if s.payload else {}
    results.append(orch_cli.execute(cfg, s.pipeline, args_dict))
  return results

