"""Orchestration layer: the agent step.

route → call → validate (schema + extra checks) → retry once with the exact
errors → fall back to the next agent on infrastructure failures.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from noetic.orchestration.run import PipelineError, Run
from noetic.tools import prompts
from noetic.agents.runners import INFRA_ERRORS, available, known_agents, run_agent
from noetic.tools.schema_check import check


def agent_step(
  run: Run, step: str, node: str, prompt: str, schema_name: str, *,
  agent: str | None = None, web: bool = False, write: bool = False, cwd: Path | None = None,
  extra_check: Callable[[dict], list[str]] | None = None, timeout: int = 900,
) -> dict:
  """Run one agent node and return JSON that has passed validation.

  node      routing key: config `steps[node]` first, then the ordered config `agents` list;
            with neither configured, the first installed adapter is used
  agent     force a specific agent (disables fallback)
  write     the agent may edit files in `cwd` (build steps); never retried blindly
  """
  cfg = run.cfg
  schema = prompts.schema(schema_name)
  if agent:
    order = [agent]
  else:
    order = cfg.agent_order(node)
    if not order:
      order = [a for a in known_agents(cfg.commands) if available(a, cfg.commands)]
    if not order:
      raise PipelineError("NO_AGENT", "no agent configured or installed; set `agents` in taste-engine.config.json "
                                      "or define a `commands` entry", step=step)
  last = None

  for name in order:
    fix = ""
    for attempt in (1, 2):
      res = run_agent(name, prompt + fix, schema, cwd=cwd or cfg.vault, web=web, write=write,
                      timeout=timeout, model=cfg.models.get(name), commands=cfg.commands)
      info = {"agent": name, "attempt": attempt, "ok": res.ok, "seconds": res.seconds, "cost_usd": res.cost_usd}
      if not res.ok:
        info["error"] = res.error
        run.log_attempt(step, info)
        last = res.error
        print(f"    ✗ {name}: {res.error['code']}: {res.error['detail'][:140]}")
        if res.error["code"] in INFRA_ERRORS or write:
          break  # infrastructure problem → next agent
        fix = "\n\nYour previous reply contained no usable JSON. Return ONLY the JSON object."
        continue
      problems = check(res.data, schema) + (extra_check(res.data) if extra_check else [])
      if not problems:
        info["validated"] = True
        run.log_attempt(step, info)
        run.set_agent(step, name)
        run.add_notes(step, name, res.data.get("harness_notes") or [])
        cost = f", ${res.cost_usd:.3f}" if res.cost_usd else ""
        print(f"    ✓ {name} ({res.seconds}s{cost})")
        return res.data
      info["schema_errors"] = problems
      run.log_attempt(step, info)
      last = {"code": "SCHEMA_INVALID", "agent": name, "detail": "; ".join(problems)}
      print(f"    ✗ {name}: output failed validation ({len(problems)} issues), retrying")
      fix = ("\n\nYour previous JSON failed validation. Fix exactly these problems and return the full corrected JSON:\n- "
             + "\n- ".join(problems))
  last = last or {"code": "NO_AGENT", "detail": "no agent produced valid output"}
  raise PipelineError(last.get("code", "FAILED"), str(last.get("detail", "")), agent=last.get("agent"))
