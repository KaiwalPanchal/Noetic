"""Orchestration layer: bounded evaluator-optimizer loop executor.

Loops are allowed only through run_loop, always budgeted by max_iterations
and optionally max_seconds. Python owns control flow and run state is resumable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import time
from typing import Any, Callable

from noetic.orchestration.run import Run


@dataclass
class Verdict:
  ok: bool
  feedback: str = ""


@dataclass
class LoopResult:
  result: Any
  verdict: Verdict
  iterations: int
  stopped_by: str  # "passed" | "max_iterations" | "max_seconds"


def run_loop(
    run: Run,
    name: str,
    act: Callable[[int, str], Any],
    evaluate: Callable[[int, Any], Verdict],
    *,
    max_iterations: int,
    max_seconds: float | None = None,
) -> LoopResult:
  """Execute a bounded evaluator-optimizer loop with step caching and budget limits."""
  if max_iterations < 1:
    raise ValueError("max_iterations must be >= 1")

  start_time = time.monotonic()
  feedback = ""
  last_result = None
  last_verdict = Verdict(ok=False)

  for i in range(1, max_iterations + 1):
    result = run.step(f"{name}-act-{i}", lambda fb=feedback, n=i: act(n, fb))
    last_result = result

    verdict_dict = run.step(
        f"{name}-eval-{i}",
        lambda res=result, n=i: asdict(evaluate(n, res)),
    )
    verdict = Verdict(**verdict_dict)
    last_verdict = verdict

    if verdict.ok:
      return LoopResult(result=result, verdict=verdict, iterations=i, stopped_by="passed")

    feedback = verdict.feedback

    # Check timeout between iterations only
    if i < max_iterations and max_seconds is not None and (time.monotonic() - start_time >= max_seconds):
      return LoopResult(result=result, verdict=verdict, iterations=i, stopped_by="max_seconds")

  return LoopResult(result=last_result, verdict=last_verdict, iterations=max_iterations, stopped_by="max_iterations")
