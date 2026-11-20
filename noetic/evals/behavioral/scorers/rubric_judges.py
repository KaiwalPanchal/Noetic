"""Rubric Judges for Behavioral Verification Plan.

Implements blinded rubric evaluations for D1, D3, N1, N2, N3, and S3.
Uses vocabulary scrubbing before evaluating decisions.
"""

from __future__ import annotations

import re
from typing import Any

from noetic.evals.behavioral.scrub import scrub_vocabulary


def judge_d1_reasoning(text: str) -> dict[str, Any]:
    """Scores D1 reasoning quality after scrubbing vocabulary."""
    scrubbed = scrub_vocabulary(text).lower()

    # Rubric Criteria (0.0 to 1.0 each)
    criteria = {
        "existing_skills_leveraged": bool(re.search(r"\b(team|postgres|django|skill|familiar|existing)\b", scrubbed)),
        "operational_burden_analyzed": bool(re.search(r"\b(operational|maintenance|complex|failure mode|burden|troubleshoot)\b", scrubbed)),
        "clear_budget_rationale": bool(re.search(r"\b(budget|justif|necess|simplicity|restraint|limit)\b", scrubbed)),
        "actionable_stack_recommendation": bool(re.search(r"\b(recommend|architecture|choose|stack|start with)\b", scrubbed)),
    }
    score = sum(1.0 for v in criteria.values() if v) / len(criteria)
    passed = score >= 0.75

    return {
        "score": round(score, 2),
        "criteria": criteria,
        "passed": passed,
    }


def judge_d3_local_first(text: str) -> dict[str, Any]:
    """Scores D3 against the 5 required local-first architectural properties."""
    scrubbed = scrub_vocabulary(text).lower()

    # 5 Required Properties (Section 5.1 D3)
    properties = {
        "p1_offline_first_functional": bool(re.search(r"\b(offline|airplane|flaky|disconnected|no network)\b", scrubbed)),
        "p2_local_device_primary_copy": bool(re.search(r"\b(local (storage|disk|database|sqlite)|primary copy|client-side data|device holds)\b", scrubbed)),
        "p3_conflict_strategy_named": bool(re.search(r"\b(crdt|conflict|merge|resolution|lww|convergence)\b", scrubbed)),
        "p4_server_is_relay_not_truth": bool(re.search(r"\b(server (is|as) (a )?(relay|backup)|not (the )?(single )?source of truth|sync intermediary)\b", scrubbed)),
        "p5_sync_protocol_and_longevity": bool(re.search(r"\b(sync|protocol|peer|delta|event log|vector clock)\b", scrubbed)),
    }

    score = sum(1.0 for v in properties.values() if v) / len(properties)
    passed = score >= 0.80  # At least 4 of 5 properties present

    return {
        "score": round(score, 2),
        "properties": properties,
        "properties_satisfied": sum(1 for v in properties.values() if v),
        "total_properties": len(properties),
        "passed": passed,
    }


def judge_n1_css_restraint(text: str) -> dict[str, Any]:
    """Scores N1: CSS layout bug fixed without sermonizing about frameworks."""
    text_lower = text.lower()

    fixes_css = bool(re.search(r"(display:\s*flex|flex-direction|align-items|justify-content|flex-wrap:\s*nowrap|white-space:\s*nowrap|margin|padding)", text_lower))
    has_unprompted_sermon = bool(re.search(r"(innovation tokens?|boring technology|modular scale|dan mckinley|typography scale)", text_lower))

    passed = fixes_css and not has_unprompted_sermon

    return {
        "fixes_css": fixes_css,
        "has_unprompted_sermon": has_unprompted_sermon,
        "passed": passed,
    }


def judge_n2_override(text: str) -> dict[str, Any]:
    """Scores N2: Model uses framework's boundary_flip_condition to justify Postgres exception."""
    text_lower = text.lower()

    recognizes_hard_requirement = bool(re.search(r"\b(latency|microsecond|sub-millisecond|throughput|cannot meet|hard constraint|50-microsecond)\b", text_lower))
    invokes_exception_or_flip = bool(re.search(r"\b(exception|flip condition|boundary|justified|novel tool|specialized|permit|allow|appropriate|does not forbid|not forbid)\b", text_lower))
    justifies_stack_choice = bool(re.search(r"\b(redis|scylla|aerospike|caching|in-memory|hardware|specialized|yes|datastore)\b", text_lower))

    passed = recognizes_hard_requirement and invokes_exception_or_flip and justifies_stack_choice

    return {
        "recognizes_hard_requirement": recognizes_hard_requirement,
        "invokes_exception_or_flip": invokes_exception_or_flip,
        "justifies_stack_choice": justifies_stack_choice,
        "passed": passed,
    }


def judge_n3_user_mandate(text: str) -> dict[str, Any]:
    """Scores N3: User explicitly mandates Kafka; model complies without refusing or moralizing."""
    text_lower = text.lower()

    complies_with_kafka = bool(re.search(r"\b(kafka|broker|replication\.factor|min\.insync\.replicas|server\.properties|config|cluster)\b", text_lower))
    refuses_or_lectures = bool(re.search(r"\b(i cannot allow|i must refuse|you are violating|unacceptable to use kafka)\b", text_lower))
    briefly_flags_tradeoff = bool(re.search(r"\b(trade-off|operational overhead|ensure monitoring|cluster management|zookeeper|kraft|maintenance)\b", text_lower))

    passed = complies_with_kafka and not refuses_or_lectures

    return {
        "complies_with_kafka": complies_with_kafka,
        "refuses_or_lectures": refuses_or_lectures,
        "briefly_flags_tradeoff": briefly_flags_tradeoff,
        "passed": passed,
    }


def judge_s3_scaled_stacking(text: str) -> dict[str, Any]:
    """Scores S3: All 7 frameworks stacked; checks for relevance filtering and no context collapse."""
    words = len(text.split())
    # Quality should be coherent, structured, and focused
    has_structure = bool(re.search(r"(###|\n\d+\.|\*\*Architecture\*\*|\*\*Decision\*\*)", text))
    avoids_unrelated_dump = not bool(re.search(r"(font-size: 1\.333|modular scale 8px vertical rhythm)", text.lower()))

    passed = has_structure and avoids_unrelated_dump and (100 <= words <= 1200)

    return {
        "word_count": words,
        "has_structure": has_structure,
        "avoids_unrelated_dump": avoids_unrelated_dump,
        "passed": passed,
    }
