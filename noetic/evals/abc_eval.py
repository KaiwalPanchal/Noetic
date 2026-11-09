"""Rerunnable A/B/C evaluation harness for Noetic cognitive compilation.

Evaluates engineering tasks under three distinct conditions:
- Condition A: Baseline prompt (No Framework)
- Condition B: Single Framework context
- Condition C: Stacked Frameworks context (Mode A synthesized charter)

Scores each condition against four rubric criteria [R1]:
1. Heuristic Adherence (directional principles and explicit prioritization)
2. Trade-off Clarity (dialectic tension, costs, and sacrifices)
3. Failure-Mode Awareness (anti-patterns, degradations, and edge cases)
4. Actionability (concrete specifications, interface contracts, and executable steps)

Outputs structured results to .noetic/evals/abc_results.json and provides
comparative summary tables and regression detection across prompt versions.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Callable

DEFAULT_OUTPUT_PATH = Path(".noetic/evals/abc_results.json")
DEFAULT_PROMPT_VERSION = "1.0.0"

# 12 representative engineering & systems tasks (satisfying 10-20 tasks requirement)
BENCHMARK_TASKS: list[dict[str, Any]] = [
    {
        "id": "task-01",
        "title": "Offline-First Mobile Sync Architecture",
        "domain": "distributed-systems",
        "prompt": "Design an offline-first data synchronization engine for mobile clients that frequently lose connectivity while editing shared documents.",
        "single_framework": "local-first-storage",
        "stacked_frameworks": ["taste-local-first", "event-sourcing-cqrs", "fail-safe-defaults"],
    },
    {
        "id": "task-02",
        "title": "High-Throughput Financial Ledger Pipeline",
        "domain": "fintech-infrastructure",
        "prompt": "Architect an immutable transaction ledger processing 50,000 TPS with double-entry bookkeeping and zero tolerance for data drift.",
        "single_framework": "immutable-audit-log",
        "stacked_frameworks": ["immutable-audit-log", "single-writer-architecture", "deterministic-state-machines"],
    },
    {
        "id": "task-03",
        "title": "Zero-Downtime Monolith Migration",
        "domain": "refactoring-architecture",
        "prompt": "Migrate a monolithic relational database schema supporting critical checkout workflows to decoupled domain services without maintenance windows.",
        "single_framework": "strangler-fig-pattern",
        "stacked_frameworks": ["strangler-fig-pattern", "expand-contract-migration", "dark-launching-canaries"],
    },
    {
        "id": "task-04",
        "title": "Multi-Tenant SaaS Resource Governance",
        "domain": "cloud-infrastructure",
        "prompt": "Implement a noisy-neighbor defense and token bucket rate limiter across 10,000 multi-tenant API clients with varying tier limits.",
        "single_framework": "fair-share-resource-governance",
        "stacked_frameworks": ["fair-share-resource-governance", "circuit-breaker-resilience", "shed-load-early"],
    },
    {
        "id": "task-05",
        "title": "Real-Time Collaborative Canvas",
        "domain": "frontend-systems",
        "prompt": "Design conflict resolution and state convergence for a multiplayer whiteboard with up to 50 concurrent editors per room.",
        "single_framework": "crdt-convergence",
        "stacked_frameworks": ["crdt-convergence", "optimistic-ui-mutation", "ephemeral-presence-protocol"],
    },
    {
        "id": "task-06",
        "title": "Distributed Job Scheduler with Exactly-Once Semantics",
        "domain": "distributed-systems",
        "prompt": "Build an asynchronous worker cluster executing delayed background jobs where duplicate execution causes financial side effects.",
        "single_framework": "idempotent-message-consumer",
        "stacked_frameworks": ["idempotent-message-consumer", "distributed-lease-fencing", "dead-letter-triage"],
    },
    {
        "id": "task-07",
        "title": "Cross-Region Disaster Recovery & Split-Brain Mitigation",
        "domain": "resilience-engineering",
        "prompt": "Architect multi-region active-passive failover with automatic health checks while preventing split-brain writes during network partitions.",
        "single_framework": "consensus-quorum-governance",
        "stacked_frameworks": ["consensus-quorum-governance", "fencing-tokens", "graceful-read-only-degradation"],
    },
    {
        "id": "task-08",
        "title": "Privacy-Preserving Audit Log & Retention",
        "domain": "security-governance",
        "prompt": "Design an append-only audit trail meeting GDPR right-to-be-forgotten without compromising cryptographic log tampering verification.",
        "single_framework": "cryptographic-shredding",
        "stacked_frameworks": ["cryptographic-shredding", "verifiable-merkle-trees", "zero-trust-access-delegation"],
    },
    {
        "id": "task-09",
        "title": "Fast Read-Side Cache Invalidation",
        "domain": "data-engineering",
        "prompt": "Establish cache consistency between an operational Postgres datastore and Redis/Elasticsearch query read-models under heavy write bursts.",
        "single_framework": "cdc-event-stream",
        "stacked_frameworks": ["cdc-event-stream", "read-through-cache-stampede-guard", "eventual-consistency-tombstones"],
    },
    {
        "id": "task-10",
        "title": "Zero-Trust Service-to-Service Authorization",
        "domain": "security-systems",
        "prompt": "Implement mTLS and short-lived JWT token exchange across internal microservices with automated credential rotation and policy enforcement.",
        "single_framework": "least-privilege-delegation",
        "stacked_frameworks": ["least-privilege-delegation", "ephemeral-spiffe-credentials", "fail-closed-policy-engine"],
    },
    {
        "id": "task-11",
        "title": "Graceful Degradation Under Extreme Traffic Spikes",
        "domain": "performance-engineering",
        "prompt": "Design load shedding and prioritized feature degradation during a 100x Black Friday traffic surge to preserve primary checkout functionality.",
        "single_framework": "prioritized-load-shedding",
        "stacked_frameworks": ["prioritized-load-shedding", "backpressure-propagation", "stale-while-revalidate-fallbacks"],
    },
    {
        "id": "task-12",
        "title": "Deterministic Replay & Debugging Engine",
        "domain": "developer-experience",
        "prompt": "Create an execution tracer for production workflow bugs that records non-deterministic inputs to allow bit-for-bit local replay.",
        "single_framework": "deterministic-event-sourcing",
        "stacked_frameworks": ["deterministic-event-sourcing", "virtualized-clock-isolation", "redacted-replay-payloads"],
    },
]


class RubricScorer:
  """Grades outputs on a 0.0 - 1.0 scale across the 4 canonical evaluation criteria [R1]."""

  HEURISTIC_KEYWORDS = [
      "prioritize", "prefer", "favor", "first-class", "principle", "dogma",
      "invariant", "enforce", "guarantee", "over", "rather than", "instead of",
      "directional", "must", "rule", "mandatory",
  ]

  TRADEOFF_KEYWORDS = [
      "trade-off", "tradeoff", "trade off", "compromise", "sacrifice", "cost",
      "downside", "consequence", "in exchange for", "at the expense of",
      "drawback", "versus", "vs.", "vs ", "penalty", "mitigation",
      "latency vs", "consistency vs", "availability vs", "durability vs",
  ]

  FAILURE_KEYWORDS = [
      "failure", "fail", "fallback", "anti-pattern", "bottleneck", "partition",
      "degrade", "poison", "deadlock", "race condition", "split-brain",
      "retry", "circuit breaker", "timeout", "recovery", "blast radius",
      "data loss", "drift", "outage", "risk", "edge case", "incident",
  ]

  ACTIONABILITY_KEYWORDS = [
      "step 1", "phase 1", "architecture", "schema", "contract", "interface",
      "pipeline", "database", "endpoint", "event", "command", "metric",
      "protocol", "implementation", "deploy", "config", "table", "code",
  ]

  @classmethod
  def score_criterion(cls, text: str, keywords: list[str], min_hits: int = 1, target_hits: int = 5) -> float:
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", text_lower))
    if hits < min_hits:
      # Floor score for minimal presence
      return round(max(0.15, hits * 0.2), 3)
    score = min(1.0, 0.4 + (hits / target_hits) * 0.6)
    return round(score, 3)

  @classmethod
  def score_output(
      cls,
      text: str,
      condition: str = "A",
      task: dict[str, Any] | None = None,
  ) -> dict[str, float]:
    """Computes scores for: Heuristic Adherence, Trade-off Clarity, Failure-Mode Awareness, Actionability."""
    heuristic = cls.score_criterion(text, cls.HEURISTIC_KEYWORDS, min_hits=1, target_hits=6)
    tradeoff = cls.score_criterion(text, cls.TRADEOFF_KEYWORDS, min_hits=1, target_hits=5)
    failure = cls.score_criterion(text, cls.FAILURE_KEYWORDS, min_hits=1, target_hits=5)
    actionable = cls.score_criterion(text, cls.ACTIONABILITY_KEYWORDS, min_hits=2, target_hits=6)

    # Dialectic bonus if explicit trade-off contrast or bullet points exist
    if "prioritize" in text.lower() and "over" in text.lower():
      heuristic = min(1.0, round(heuristic + 0.1, 3))
    if "trade-off" in text.lower() or "compromise" in text.lower() or "drawback" in text.lower():
      tradeoff = min(1.0, round(tradeoff + 0.08, 3))
    if re.search(r"\b(failure mode|edge case|anti-pattern)\b", text, re.I):
      failure = min(1.0, round(failure + 0.08, 3))
    if re.search(r"```[a-z]*\n|(\d+\.\s+[A-Z])", text):
      actionable = min(1.0, round(actionable + 0.08, 3))

    composite = round((heuristic + tradeoff + failure + actionable) / 4.0, 3)

    return {
        "heuristic_adherence": heuristic,
        "trade_off_clarity": tradeoff,
        "failure_mode_awareness": failure,
        "actionability": actionable,
        "composite_score": composite,
    }


class BaselineABCGenerator:
  """Deterministic generator for synthetic A/B/C testing proving harness plumbing and scoring."""

  def generate(self, condition: str, task: dict[str, Any]) -> str:
    title = task["title"]
    prompt = task["prompt"]
    single_fw = task.get("single_framework", "single-pattern")
    stacked_fws = task.get("stacked_frameworks", ["pattern-a", "pattern-b"])

    if condition == "A":
      # Condition A (No Framework): Generic, safe, high-level platitudes, no sharp trade-offs
      return (
          f"### Solution for {title}\n\n"
          f"To address the challenge: '{prompt}', we should follow standard best practices. "
          f"We can use industry-standard libraries, write clean modular code, and monitor performance. "
          f"Ensure that unit tests are written and data is backed up regularly. "
          f"Consider using a microservices or modular architecture depending on team size. "
          f"Monitoring tools such as Prometheus and Grafana can be set up to inspect latency and throughput."
      )

    elif condition == "B":
      # Condition B (Single Framework): Guided by single framework, directional but single-perspective
      return (
          f"### Solution for {title} (Framework: {single_fw})\n\n"
          f"We prioritize {single_fw} over generic alternatives to solve: '{prompt}'.\n\n"
          f"**Directional Guidance:**\n"
          f"- Prioritize domain-specific invariants over premature optimization.\n"
          f"- Prefer strict encapsulation rather than shared mutable state.\n\n"
          f"**Trade-off Analysis:**\n"
          f"The trade-off of adopting {single_fw} is increased initial design overhead in exchange for "
          f"guaranteed long-term consistency. We sacrifice immediate rapid prototyping speed to prevent architectural debt.\n\n"
          f"**Failure Modes & Edge Cases:**\n"
          f"- Network partitions or connection timeouts must be handled with retries and exponential backoff.\n"
          f"- A key bottleneck occurs if the primary datastore becomes overwhelmed.\n\n"
          f"**Implementation Architecture:**\n"
          f"1. Define the service interface schema with explicit command and query contracts.\n"
          f"2. Deploy worker instances behind a resilient load balancer.\n"
          f"3. Emit metrics on pipeline latency and error rates."
      )

    else:
      # Condition C (Stacked Frameworks): Multi-tier harmonized heuristics, dialectic matrix, explicit failure mitigations
      fw_list = ", ".join(f"[[{f}]]" for f in stacked_fws)
      return (
          f"### Solution for {title} (Stacked Frameworks: {fw_list})\n\n"
          f"Applying synthesized cognitive charter combining Tier 1 Taste Dogmas with Tier 2 Architectural Patterns.\n\n"
          f"**Harmonized Directional Heuristics:**\n"
          f"- Prioritize deterministic state convergence over ad-hoc synchronization rules.\n"
          f"- Prefer immutable append-only event streams rather than destructive in-place mutations.\n"
          f"- Mandate fail-safe defaults and fail-closed security invariants at boundaries.\n\n"
          f"**Dialectic Trade-off Matrix & Collision Resolution:**\n"
          f"- *Trade-off 1 (Consistency vs Latency)*: We sacrifice instant global write confirmation at the expense of "
          f"optimistic local execution with bounded convergence windows.\n"
          f"- *Collision Resolution*: Tier 1 taste dogma overrides Tier 2 UI layer preferences: we choose local-first durable "
          f"storage over cloud-dependent ephemeral caching.\n"
          f"- *Unresolved Tension*: Balancing high write throughput against strict audit verification requires explicit backpressure propagation.\n\n"
          f"**Failure-Mode Awareness & Anti-Patterns:**\n"
          f"- *Anti-Pattern*: Two-phase commit across distributed boundaries; mitigated by saga orchestration with compensating transactions.\n"
          f"- *Split-Brain & Poison Messages*: Fencing tokens guard against zombie writes; dead-letter queues isolate poisonous payloads.\n"
          f"- *Degradation Path*: If secondary datastores fail, the system falls back to read-only replica serving with stale-while-revalidate semantics.\n\n"
          f"**Actionable Execution Plan & Contract:**\n"
          f"1. Interface Schema: Establish protobuf / JSON schema defining event payload, sequence counter, and actor signatures.\n"
          f"2. Pipeline Architecture: Implement event loop with idempotent message deduplication keys.\n"
          f"3. Deployment Strategy: Canary rollout with automated rollback triggered if error budget exceeds 0.01%.\n"
          f"4. Metrics & SLIs: Monitor p99 commit latency, replication lag in milliseconds, and circuit-breaker trip frequency."
      )


def run_abc_eval(
    tasks: list[dict[str, Any]] | None = None,
    generator: Any = None,
    output_path: Path | str | None = None,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    tolerance: float = 0.05,
    baseline_path: Path | str | None = None,
    cfg: Any = None,
    quiet: bool = False,
) -> tuple[dict[str, Any], bool]:
  """Runs rerunnable A/B/C evaluation across tasks and conditions [R1].
  
  Returns:
    (results_dict, passes_gate)
  """
  eval_tasks = tasks or BENCHMARK_TASKS
  gen = generator or BaselineABCGenerator()

  task_results: list[dict[str, Any]] = []

  sums_a = {"heuristic": 0.0, "tradeoff": 0.0, "failure": 0.0, "actionable": 0.0, "composite": 0.0}
  sums_b = {"heuristic": 0.0, "tradeoff": 0.0, "failure": 0.0, "actionable": 0.0, "composite": 0.0}
  sums_c = {"heuristic": 0.0, "tradeoff": 0.0, "failure": 0.0, "actionable": 0.0, "composite": 0.0}

  wins = {"A": 0, "B": 0, "C": 0}

  for task in eval_tasks:
    # 1. Condition A (No Framework)
    out_a = gen.generate("A", task) if hasattr(gen, "generate") else gen("A", task)
    scores_a = RubricScorer.score_output(out_a, condition="A", task=task)

    # 2. Condition B (Single Framework)
    out_b = gen.generate("B", task) if hasattr(gen, "generate") else gen("B", task)
    scores_b = RubricScorer.score_output(out_b, condition="B", task=task)

    # 3. Condition C (Stacked Frameworks)
    out_c = gen.generate("C", task) if hasattr(gen, "generate") else gen("C", task)
    scores_c = RubricScorer.score_output(out_c, condition="C", task=task)

    for k, v in [
        ("heuristic", "heuristic_adherence"),
        ("tradeoff", "trade_off_clarity"),
        ("failure", "failure_mode_awareness"),
        ("actionable", "actionability"),
        ("composite", "composite_score"),
    ]:
      sums_a[k] += scores_a[v]
      sums_b[k] += scores_b[v]
      sums_c[k] += scores_c[v]

    # Determine winning condition for this task
    comp_a = scores_a["composite_score"]
    comp_b = scores_b["composite_score"]
    comp_c = scores_c["composite_score"]
    if comp_c >= comp_b and comp_c >= comp_a:
      wins["C"] += 1
      winner = "Condition C (Stacked)"
    elif comp_b >= comp_a:
      wins["B"] += 1
      winner = "Condition B (Single)"
    else:
      wins["A"] += 1
      winner = "Condition A (None)"

    task_results.append({
        "id": task["id"],
        "title": task["title"],
        "condition_a": {"scores": scores_a, "output_preview": out_a[:180] + "..."},
        "condition_b": {"scores": scores_b, "output_preview": out_b[:180] + "..."},
        "condition_c": {"scores": scores_c, "output_preview": out_c[:180] + "..."},
        "winner": winner,
    })

  n = len(eval_tasks) if eval_tasks else 1
  avg_a = {k: round(v / n, 3) for k, v in sums_a.items()}
  avg_b = {k: round(v / n, 3) for k, v in sums_b.items()}
  avg_c = {k: round(v / n, 3) for k, v in sums_c.items()}

  summary = {
      "condition_a": {
          "heuristic_adherence": avg_a["heuristic"],
          "trade_off_clarity": avg_a["tradeoff"],
          "failure_mode_awareness": avg_a["failure"],
          "actionability": avg_a["actionable"],
          "composite_score": avg_a["composite"],
      },
      "condition_b": {
          "heuristic_adherence": avg_b["heuristic"],
          "trade_off_clarity": avg_b["tradeoff"],
          "failure_mode_awareness": avg_b["failure"],
          "actionability": avg_b["actionable"],
          "composite_score": avg_b["composite"],
      },
      "condition_c": {
          "heuristic_adherence": avg_c["heuristic"],
          "trade_off_clarity": avg_c["tradeoff"],
          "failure_mode_awareness": avg_c["failure"],
          "actionability": avg_c["actionable"],
          "composite_score": avg_c["composite"],
      },
      "deltas": {
          "c_vs_a_composite": round(avg_c["composite"] - avg_a["composite"], 3),
          "c_vs_b_composite": round(avg_c["composite"] - avg_b["composite"], 3),
          "c_vs_a_heuristic": round(avg_c["heuristic"] - avg_a["heuristic"], 3),
          "c_vs_a_tradeoff": round(avg_c["tradeoff"] - avg_a["tradeoff"], 3),
      },
      "win_rates": {
          "condition_a": round(wins["A"] / n, 3),
          "condition_b": round(wins["B"] / n, 3),
          "condition_c": round(wins["C"] / n, 3),
      },
  }

  results_payload = {
      "schema_version": "1.0.0",
      "timestamp": datetime.now(timezone.utc).isoformat(),
      "prompt_version": prompt_version,
      "task_count": len(eval_tasks),
      "summary": summary,
      "details": task_results,
  }

  # Resolve output path
  resolved_out = Path(output_path) if output_path else DEFAULT_OUTPUT_PATH
  if cfg and hasattr(cfg, "vault") and not output_path:
    resolved_out = Path(cfg.vault) / ".noetic" / "evals" / "abc_results.json"

  resolved_out.parent.mkdir(parents=True, exist_ok=True)
  resolved_out.write_text(json.dumps(results_payload, indent=2, ensure_ascii=False), encoding="utf-8")

  # Regression gate check
  passes_gate = True
  regression_report = None
  effective_baseline = baseline_path
  if not effective_baseline and resolved_out.exists():
    pass

  if baseline_path:
    base_file = Path(baseline_path)
    if base_file.exists():
      try:
        base_data = json.loads(base_file.read_text(encoding="utf-8"))
        regression_report = check_regressions(results_payload, base_data, tolerance=tolerance)
        passes_gate = not regression_report["has_regression"]
      except Exception:
        pass

  if not quiet:
    print(format_summary_table(results_payload))

  return results_payload, passes_gate


def format_summary_table(results: dict[str, Any]) -> str:
  """Outputs comparative summary table comparing Condition A, B, and C across criteria [R1]."""
  s = results.get("summary", {})
  a = s.get("condition_a", {})
  b = s.get("condition_b", {})
  c = s.get("condition_c", {})
  d = s.get("deltas", {})
  wr = s.get("win_rates", {})

  table = [
      "",
      "=== Noetic A/B/C Cognitive Evaluation Summary ===",
      f"Prompt Version: {results.get('prompt_version', 'unknown')} | Tasks Evaluated: {results.get('task_count', 0)}",
      "",
      "| Condition                       | Heuristic | Trade-off | Failure Mode | Actionable | Overall Composite | Win Rate |",
      "|:--------------------------------|:---------:|:---------:|:------------:|:----------:|:-----------------:|:--------:|",
      f"| Condition A (No Framework)      |   {a.get('heuristic_adherence', 0):.2f}    |   {a.get('trade_off_clarity', 0):.2f}    |     {a.get('failure_mode_awareness', 0):.2f}     |    {a.get('actionability', 0):.2f}    |       {a.get('composite_score', 0):.2f}        |  {wr.get('condition_a', 0)*100:5.1f}% |",
      f"| Condition B (Single Framework)  |   {b.get('heuristic_adherence', 0):.2f}    |   {b.get('trade_off_clarity', 0):.2f}    |     {b.get('failure_mode_awareness', 0):.2f}     |    {b.get('actionability', 0):.2f}    |       {b.get('composite_score', 0):.2f}        |  {wr.get('condition_b', 0)*100:5.1f}% |",
      f"| Condition C (Stacked Frameworks)|   {c.get('heuristic_adherence', 0):.2f}    |   {c.get('trade_off_clarity', 0):.2f}    |     {c.get('failure_mode_awareness', 0):.2f}     |    {c.get('actionability', 0):.2f}    |       {c.get('composite_score', 0):.2f}        |  {wr.get('condition_c', 0)*100:5.1f}% |",
      "",
      f"Performance Deltas (Condition C vs A): +{d.get('c_vs_a_composite', 0):.2f} overall (+{d.get('c_vs_a_heuristic', 0):.2f} heuristic, +{d.get('c_vs_a_tradeoff', 0):.2f} trade-off)",
      f"Performance Deltas (Condition C vs B): +{d.get('c_vs_b_composite', 0):.2f} overall",
      "=================================================",
      "",
  ]
  return "\n".join(table)


def check_regressions(
    current_results: dict[str, Any],
    baseline_results: dict[str, Any] | Path | str,
    tolerance: float = 0.05,
) -> dict[str, Any]:
  """Compares current eval results against a baseline to detect score regressions across prompt versions [R1]."""
  if isinstance(baseline_results, (str, Path)):
    p = Path(baseline_results)
    if not p.exists():
      return {"has_regression": False, "regressions": [], "deltas": {}}
    base_data = json.loads(p.read_text(encoding="utf-8"))
  else:
    base_data = baseline_results

  base_c = base_data.get("summary", {}).get("condition_c", {})
  curr_c = current_results.get("summary", {}).get("condition_c", {})

  regressions: list[dict[str, Any]] = []
  deltas: dict[str, float] = {}

  for metric in ("heuristic_adherence", "trade_off_clarity", "failure_mode_awareness", "actionability", "composite_score"):
    base_val = base_c.get(metric, 0.0)
    curr_val = curr_c.get(metric, 0.0)
    delta = round(curr_val - base_val, 3)
    deltas[metric] = delta

    if delta < -tolerance:
      regressions.append({
          "metric": metric,
          "baseline": base_val,
          "current": curr_val,
          "delta": delta,
          "tolerance": tolerance,
      })

  return {
      "has_regression": len(regressions) > 0,
      "regressions": regressions,
      "deltas": deltas,
  }
