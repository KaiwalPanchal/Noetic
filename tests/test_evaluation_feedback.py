"""Tests for Phase 6: Evaluation & Feedback Loop [R1+R2].

Covers:
1. Rerunnable A/B/C evaluation harness (noetic/evals/abc_eval.py)
   - Evaluates tasks under Condition A (No Framework), Condition B (Single), Condition C (Stacked)
   - Scores outputs across rubric criteria: Heuristic adherence, trade-off clarity,
     failure-mode awareness, actionability
   - Saves structured results to abc_results.json
   - Comparative summary table formatting
   - Regression detection across prompt versions
2. Applications Log adoption tracking (noetic/knowledge/notes.py)
   - Outcome recording: followed, overridden, regretted
   - Machine log marker protection & approval hash invariance
   - Framework confidence indicator calculation
3. Contradiction tracking in Knowledge Graph (noetic/knowledge/graph.py)
   - Persistent records in frameworks/.index/contradictions.json & graph.json
   - Tension capture from charter during stacking & sparring
   - Canonical ordering, deduplication, and filtering
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from noetic.evals.abc_eval import (
    BENCHMARK_TASKS,
    BaselineABCGenerator,
    RubricScorer,
    check_regressions,
    format_summary_table,
    run_abc_eval,
)
from noetic.knowledge import graph, notes
from noetic.knowledge.config import Config
from noetic.knowledge.notes import (
    LOG_END,
    LOG_START,
    append_application,
    compute_content_hash,
    framework_confidence_metric,
    set_status,
    verify_approval_hash,
)
from noetic.knowledge.stack import stack_frameworks_logic


# ─── 1. A/B/C Evaluation Harness Tests ────────────────────────────────────────

def test_abc_eval_benchmark_tasks_count():
  """Verifies that 10–20 tasks are provided in the benchmark suite [R1]."""
  assert 10 <= len(BENCHMARK_TASKS) <= 20
  for t in BENCHMARK_TASKS:
    assert "id" in t
    assert "title" in t
    assert "prompt" in t
    assert "single_framework" in t
    assert "stacked_frameworks" in t
    assert len(t["stacked_frameworks"]) >= 2


def test_abc_eval_rubric_scorer_components():
  """Tests isolated scoring of rubric criteria."""
  high_scoring_text = (
      "We prioritize local-first durability over cloud ephemeral caching. "
      "Directional principle: enforce immutable append-only logs rather than in-place mutations. "
      "Trade-off analysis: the compromise is increased storage cost at the expense of instant write latency. "
      "Failure mode: network partitions and split-brain states are mitigated with fencing tokens and timeouts. "
      "Actionable plan:\n"
      "1. Interface schema: define JSON contracts for event log.\n"
      "2. Architecture: deploy worker cluster with circuit breakers."
  )
  scores = RubricScorer.score_output(high_scoring_text, condition="C")
  assert scores["heuristic_adherence"] >= 0.7
  assert scores["trade_off_clarity"] >= 0.7
  assert scores["failure_mode_awareness"] >= 0.7
  assert scores["actionability"] >= 0.7
  assert scores["composite_score"] >= 0.75

  vague_text = "This is a general computer program. It does things cleanly and runs well."
  vague_scores = RubricScorer.score_output(vague_text, condition="A")
  assert vague_scores["composite_score"] < 0.45


def test_abc_eval_execution_and_score_comparison(tmp_path: Path):
  """Tests running A/B/C evaluation harness across all tasks and verifying Condition C superiority [R1]."""
  out_file = tmp_path / "evals" / "abc_results.json"
  results, passes_gate = run_abc_eval(output_path=out_file, quiet=True)

  assert passes_gate is True
  assert out_file.exists()

  saved_data = json.loads(out_file.read_text(encoding="utf-8"))
  assert saved_data["schema_version"] == "1.0.0"
  assert saved_data["task_count"] == len(BENCHMARK_TASKS)
  assert "summary" in saved_data
  assert len(saved_data["details"]) == len(BENCHMARK_TASKS)

  summary = saved_data["summary"]
  cond_a = summary["condition_a"]
  cond_b = summary["condition_b"]
  cond_c = summary["condition_c"]

  # Rubric criteria must all be present
  for cond in (cond_a, cond_b, cond_c):
    assert "heuristic_adherence" in cond
    assert "trade_off_clarity" in cond
    assert "failure_mode_awareness" in cond
    assert "actionability" in cond
    assert "composite_score" in cond

  # Condition C (Stacked) > Condition B (Single) > Condition A (None)
  assert cond_c["composite_score"] > cond_b["composite_score"]
  assert cond_b["composite_score"] > cond_a["composite_score"]

  # Deltas
  deltas = summary["deltas"]
  assert deltas["c_vs_a_composite"] > 0.25
  assert deltas["c_vs_b_composite"] > 0.10

  # Win rates
  assert summary["win_rates"]["condition_c"] >= 0.90


def test_abc_eval_summary_table_formatting():
  """Verifies comparative summary table formatting."""
  results, _ = run_abc_eval(tasks=BENCHMARK_TASKS[:2], quiet=True)
  table_str = format_summary_table(results)

  assert "=== Noetic A/B/C Cognitive Evaluation Summary ===" in table_str
  assert "Condition A (No Framework)" in table_str
  assert "Condition B (Single Framework)" in table_str
  assert "Condition C (Stacked Frameworks)" in table_str
  assert "Performance Deltas (Condition C vs A):" in table_str


def test_abc_eval_regression_detection(tmp_path: Path):
  """Verifies regression detection across prompt versions [R1]."""
  base_file = tmp_path / "base.json"
  results_good, _ = run_abc_eval(tasks=BENCHMARK_TASKS[:3], output_path=base_file, quiet=True)

  # Check against identical: no regression
  rep_clean = check_regressions(results_good, base_file, tolerance=0.05)
  assert rep_clean["has_regression"] is False
  assert len(rep_clean["regressions"]) == 0

  # Synthetic regressed generator
  class DegradedGenerator:
    def generate(self, condition: str, task: dict):
      return "Generic short text with no heuristics or trade-offs."

  deg_file = tmp_path / "deg.json"
  results_deg, passes_gate = run_abc_eval(
      tasks=BENCHMARK_TASKS[:3],
      generator=DegradedGenerator(),
      baseline_path=base_file,
      output_path=deg_file,
      tolerance=0.05,
      quiet=True,
  )

  assert passes_gate is False
  rep_reg = check_regressions(results_deg, base_file, tolerance=0.05)
  assert rep_reg["has_regression"] is True
  assert any(r["metric"] == "composite_score" for r in rep_reg["regressions"])


# ─── 2. Applications Log Adoption Tracking Tests ──────────────────────────────

def test_append_application_outcomes(tmp_path: Path):
  """Tests recording outcomes (followed, overridden, regretted) in applications log [R1]."""
  note_path = tmp_path / "framework-alpha.md"
  initial_text = f"""---
status: pending_review
---
# Framework: Alpha

<!-- NOETIC:LOG:START -->
## Applications Log
-
<!-- NOETIC:LOG:END -->
"""
  note_path.write_text(initial_text, encoding="utf-8")

  # 1. Followed
  append_application(note_path, "code", "project-x", outcome="followed")
  # 2. Overridden
  append_application(note_path, "writing", "essay-y", outcome="overridden")
  # 3. Regretted
  append_application(note_path, "review", "adr-z", outcome="regretted")
  # 4. Without outcome (legacy backward compatibility)
  append_application(note_path, "audit", "audit-01")

  content = note_path.read_text(encoding="utf-8")
  assert "· code · [[project-x]] · outcome: followed" in content
  assert "· writing · [[essay-y]] · outcome: overridden" in content
  assert "· review · [[adr-z]] · outcome: regretted" in content
  assert "· audit · [[audit-01]]" in content
  # Machine log markers must be preserved
  assert LOG_START in content
  assert LOG_END in content


def test_append_application_validates_outcome(tmp_path: Path):
  """Ensures invalid outcome values raise ValueError."""
  note_path = tmp_path / "framework-beta.md"
  note_path.write_text("# Beta", encoding="utf-8")

  with pytest.raises(ValueError, match="Invalid outcome"):
    append_application(note_path, "code", "ref-01", outcome="disastrous")


def test_framework_confidence_metric_calculation(tmp_path: Path):
  """Tests calculation of framework confidence indicators derived from log [R1]."""
  note_path = tmp_path / "framework-gamma.md"
  note_text = f"""---
status: approved
---
# Framework: Gamma

<!-- NOETIC:LOG:START -->
## Applications Log
- 2026-11-01 · code · [[proj-1]] · outcome: followed
- 2026-11-03 · code · [[proj-2]] · outcome: followed
- 2026-11-05 · writing · [[proj-3]] · outcome: overridden
- 2026-11-09 · refactoring · [[proj-4]] · outcome: followed
<!-- NOETIC:LOG:END -->
"""
  note_path.write_text(note_text, encoding="utf-8")

  metrics = framework_confidence_metric(tmp_path, "framework-gamma")
  assert metrics["total_applications"] == 4
  assert metrics["followed_count"] == 3
  assert metrics["override_count"] == 1
  assert metrics["regret_count"] == 0
  assert metrics["confidence_rating"] >= 0.75
  assert metrics["confidence_level"] == "high"
  assert metrics["last_validated"] == "2026-11-09"


def test_framework_confidence_metric_zero_applications(tmp_path: Path):
  """Tests confidence metrics for a framework with zero applications."""
  metrics = framework_confidence_metric(tmp_path, "non-existent")
  assert metrics["total_applications"] == 0
  assert metrics["followed_count"] == 0
  assert metrics["override_count"] == 0
  assert metrics["regret_count"] == 0
  assert metrics["confidence_rating"] == 0.0
  assert metrics["confidence_level"] == "low"
  assert metrics["last_validated"] is None


def test_framework_confidence_metric_regrets_lower_rating(tmp_path: Path):
  """Tests that regret outcomes pull confidence level down."""
  note_path = tmp_path / "framework-delta.md"
  note_text = f"""---
status: approved
---
# Framework: Delta

<!-- NOETIC:LOG:START -->
## Applications Log
- 2026-11-02 · code · [[bad-proj-1]] · outcome: regretted
- 2026-11-04 · code · [[bad-proj-2]] · outcome: regretted
- 2026-11-06 · code · [[bad-proj-3]] · outcome: overridden
<!-- NOETIC:LOG:END -->
"""
  note_path.write_text(note_text, encoding="utf-8")

  metrics = framework_confidence_metric(tmp_path, "framework-delta")
  assert metrics["total_applications"] == 3
  assert metrics["regret_count"] == 2
  assert metrics["override_count"] == 1
  assert metrics["followed_count"] == 0
  assert metrics["confidence_rating"] <= 0.2
  assert metrics["confidence_level"] == "low"


def test_approval_hash_invariant_with_applications_logging(tmp_path: Path):
  """Ensures updating applications log inside machine markers preserves cryptographic approval hash [R1]."""
  note_path = tmp_path / "framework-epsilon.md"
  initial = f"""---
status: pending_review
---
# Framework: Epsilon

## Core Directional Heuristics
- Prioritize deterministic replay over debugging live state.

<!-- NOETIC:LOG:START -->
## Applications Log
-
<!-- NOETIC:LOG:END -->
"""
  note_path.write_text(initial, encoding="utf-8")

  # Approve the note (calculates approval_hash)
  set_status(note_path, "approved")
  assert verify_approval_hash(note_path) is True

  # Append an application inside log markers
  append_application(note_path, "code", "app-demo", outcome="followed")

  # Approval hash MUST remain valid because log block is normalized away
  assert verify_approval_hash(note_path) is True


# ─── 3. Contradiction Tracking in Knowledge Graph Tests ───────────────────────

def test_record_contradiction_persistence(tmp_path: Path):
  """Tests recording contradiction records in frameworks/.index/contradictions.json [R1]."""
  cfg = Config(tmp_path, {})
  rec = graph.record_contradiction(
      cfg,
      framework_a="local-first-storage",
      framework_b="cloud-centralized-sync",
      tension_point="local durability vs central authority",
      competing_heuristics=[
          "local-first: Prioritize client writes over server coordination",
          "cloud-centralized: Prioritize central server coordination over local divergence",
      ],
      source="unit_test",
  )

  index_dir = tmp_path / "frameworks" / ".index"
  c_file = index_dir / "contradictions.json"
  g_file = index_dir / "graph.json"

  assert c_file.exists()
  assert g_file.exists()

  data = json.loads(c_file.read_text(encoding="utf-8"))
  assert isinstance(data, list)
  assert len(data) == 1
  assert data[0]["framework_a"] == "cloud-centralized-sync"
  assert data[0]["framework_b"] == "local-first-storage"
  assert data[0]["tension_point"] == "local durability vs central authority"
  assert len(data[0]["competing_heuristics"]) == 2

  # Check graph.json edges
  graph_data = json.loads(g_file.read_text(encoding="utf-8"))
  assert graph_data["schema_version"] == "1.0.0"
  assert len(graph_data["edges"]) == 1
  assert graph_data["edges"][0]["type"] == "contradiction"


def test_record_contradiction_canonical_ordering_and_deduplication(tmp_path: Path):
  """Verifies that reversed arguments update the existing contradiction instead of duplicating [R1]."""
  cfg = Config(tmp_path, {})

  # First call (A, B)
  graph.record_contradiction(
      cfg,
      framework_a="framework-one",
      framework_b="framework-two",
      tension_point="memory vs disk",
      competing_heuristics=["Heuristic 1"],
  )

  # Second call (B, A) with same tension point
  graph.record_contradiction(
      cfg,
      framework_a="framework-two",
      framework_b="framework-one",
      tension_point="memory vs disk",
      competing_heuristics=["Heuristic 2"],
  )

  contradictions = graph.get_contradictions(cfg)
  assert len(contradictions) == 1
  assert set(contradictions[0]["competing_heuristics"]) == {"Heuristic 1", "Heuristic 2"}


def test_get_contradictions_filtering(tmp_path: Path):
  """Tests querying contradictions filtered by framework slug."""
  cfg = Config(tmp_path, {})
  graph.record_contradiction(cfg, "fw-a", "fw-b", "tension 1")
  graph.record_contradiction(cfg, "fw-b", "fw-c", "tension 2")
  graph.record_contradiction(cfg, "fw-c", "fw-d", "tension 3")

  all_c = graph.get_contradictions(cfg)
  assert len(all_c) == 3

  b_c = graph.get_contradictions(cfg, framework="fw-b")
  assert len(b_c) == 2
  assert all("fw-b" in (r["framework_a"], r["framework_b"]) for r in b_c)

  d_c = graph.get_contradictions(cfg, framework="fw-d")
  assert len(d_c) == 1
  assert d_c[0]["tension_point"] == "tension 3"


def test_record_tensions_from_charter(tmp_path: Path):
  """Tests capturing tensions directly from synthesis charter [R1]."""
  cfg = Config(tmp_path, {})
  charter = {
      "unresolved_tensions": [
          {
              "tension_dimension": "offline mutation vs instant consistency",
              "conflicting_frameworks": ["alpha-sync", "beta-cluster"],
              "conflicting_heuristics": ["Prioritize offline", "Prioritize cluster"],
          }
      ],
      "resolved_collisions": [
          {
              "collision_dimension": "storage layer tier conflict",
              "frameworks_involved": ["tier1-taste", "tier3-ui"],
              "winning_framework": "tier1-taste",
              "tier_domain_rationale": "Tier 1 overrides Tier 3",
          }
      ],
  }

  recorded = graph.record_tensions_from_charter(cfg, charter, source="charter_test")
  assert len(recorded) == 2

  stored = graph.get_contradictions(cfg)
  assert len(stored) == 2
  assert any(r["framework_a"] == "alpha-sync" and r["framework_b"] == "beta-cluster" for r in stored)


def test_stack_frameworks_logic_persists_contradictions(tmp_path: Path):
  """Integration: ensures stack_frameworks_logic records detected tensions to .index/contradictions.json [R1]."""
  cfg = Config(tmp_path, {})
  fw_dir = cfg.frameworks
  fw_dir.mkdir(parents=True, exist_ok=True)

  # Create Framework 1: Tier 2, domain storage, local
  f1_text = """---
status: approved
---
# Framework: Offline First
**Tags:** storage, sync

## Core Directional Heuristics
- Tier 2 | Prioritize local storage over remote database. Context: offline-first apps.
"""
  f1_path = fw_dir / "offline-first.md"
  f1_path.write_text(f1_text, encoding="utf-8")
  set_status(f1_path, "approved")

  # Create Framework 2: Tier 2, domain storage, cloud (opposing antonym)
  f2_text = """---
status: approved
---
# Framework: Cloud Centralized
**Tags:** storage, sync

## Core Directional Heuristics
- Tier 2 | Prioritize remote database over local storage. Context: multi-tenant SaaS.
"""
  f2_path = fw_dir / "cloud-centralized.md"
  f2_path.write_text(f2_text, encoding="utf-8")
  set_status(f2_path, "approved")

  # Stack the frameworks without order precedence flag -> emits unresolved tension
  charter = stack_frameworks_logic(cfg, ["offline-first", "cloud-centralized"], allow_order_precedence=False)
  assert len(charter["unresolved_tensions"]) >= 1

  # Contradiction must now be persistently stored in .index/contradictions.json
  stored_contradictions = graph.get_contradictions(cfg)
  assert len(stored_contradictions) >= 1
  assert any(
      "offline-first" in (r["framework_a"], r["framework_b"])
      and "cloud-centralized" in (r["framework_a"], r["framework_b"])
      for r in stored_contradictions
  )
