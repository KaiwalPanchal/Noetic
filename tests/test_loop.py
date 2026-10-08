"""Tests for noetic.orchestration.loop (bounded loop executor)."""

from __future__ import annotations

import time
import pytest

from noetic.orchestration.loop import LoopResult, Verdict, run_loop
from noetic.orchestration.run import Run


def test_loop_passes_on_iteration_2(cfg):
  run = Run(cfg, "test_pass_iter2", {})
  act_calls = []

  def act(i: int, fb: str) -> dict:
    act_calls.append(i)
    return {"iteration": i, "data": f"result-{i}"}

  def evaluate(i: int, res: dict) -> Verdict:
    if i == 2:
      return Verdict(ok=True)
    return Verdict(ok=False, feedback="need another try")

  result = run_loop(run, "test", act, evaluate, max_iterations=3)
  assert result.stopped_by == "passed"
  assert result.iterations == 2
  assert result.verdict.ok is True
  assert act_calls == [1, 2]


def test_loop_exhausts_at_max_iterations(cfg):
  run = Run(cfg, "test_exhaust", {})

  def act(i: int, fb: str) -> dict:
    return {"iteration": i}

  def evaluate(i: int, res: dict) -> Verdict:
    return Verdict(ok=False, feedback="still failing")

  result = run_loop(run, "test", act, evaluate, max_iterations=3)
  assert result.stopped_by == "max_iterations"
  assert result.iterations == 3
  assert result.verdict.ok is False
  assert result.verdict.feedback == "still failing"


def test_loop_max_seconds_stops_after_iteration_1(cfg, monkeypatch):
  run = Run(cfg, "test_timeout", {})
  current_time = [100.0]

  def fake_monotonic():
    return current_time[0]

  monkeypatch.setattr(time, "monotonic", fake_monotonic)

  def act(i: int, fb: str) -> dict:
    # Advance time during act
    current_time[0] += 5.0
    return {"iteration": i}

  def evaluate(i: int, res: dict) -> Verdict:
    return Verdict(ok=False, feedback="retry")

  # max_seconds=0 means between iterations 1 and 2, elapsed >= 0 is met
  result = run_loop(run, "test", act, evaluate, max_iterations=3, max_seconds=0)
  assert result.stopped_by == "max_seconds"
  assert result.iterations == 1


def test_loop_max_iterations_zero_raises(cfg):
  run = Run(cfg, "test_invalid_iterations", {})
  with pytest.raises(ValueError) as exc:
    run_loop(run, "test", lambda i, fb: {}, lambda i, res: Verdict(ok=True), max_iterations=0)
  assert "max_iterations must be >= 1" in str(exc.value)


def test_loop_resumes_without_recalling_act(cfg):
  run1 = Run(cfg, "test_resume", {})
  act1_calls = []

  def act1(i: int, fb: str) -> dict:
    act1_calls.append(i)
    return {"iteration": i}

  def eval1(i: int, res: dict) -> Verdict:
    return Verdict(ok=False, feedback="try again")

  # Run only 1 iteration
  res1 = run_loop(run1, "test", act1, eval1, max_iterations=1)
  assert res1.iterations == 1
  assert act1_calls == [1]

  # Now resume the run with max_iterations=2
  run2 = Run(cfg, "test_resume", {}, run_id=run1.id)
  act2_calls = []

  def act2(i: int, fb: str) -> dict:
    act2_calls.append(i)
    return {"iteration": i}

  def eval2(i: int, res: dict) -> Verdict:
    if i == 2:
      return Verdict(ok=True)
    return Verdict(ok=False, feedback="try again")

  res2 = run_loop(run2, "test", act2, eval2, max_iterations=2)
  assert res2.stopped_by == "passed"
  assert res2.iterations == 2
  # act2 should only have been called for iteration 2!
  assert act2_calls == [2]


def test_loop_feedback_reaches_next_iteration(cfg):
  run = Run(cfg, "test_feedback", {})
  feedbacks_received = []

  def act(i: int, fb: str) -> dict:
    feedbacks_received.append(fb)
    return {"step": i}

  def evaluate(i: int, res: dict) -> Verdict:
    if i == 3:
      return Verdict(ok=True)
    return Verdict(ok=False, feedback=f"error-at-{i}")

  result = run_loop(run, "test", act, evaluate, max_iterations=3)
  assert result.stopped_by == "passed"
  assert feedbacks_received == ["", "error-at-1", "error-at-2"]
