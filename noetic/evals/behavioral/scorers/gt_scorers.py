"""Ground-Truth (GT) Scorers for Behavioral Verification Plan.

Implements pre-registered ground-truth evaluation for D2, R1, R2, and R3.
"""

from __future__ import annotations

import json
import re
from typing import Any

from noetic.evals.abc_eval import RubricScorer


# ── D2: Decision Reversibility Ground Truth Labels ──────────────────────────

D2_GROUND_TRUTH = {
    1: "Hat",       # rename a local variable
    2: "Haircut",   # choose primary key type (UUIDv7 vs bigint)
    3: "Tattoo",    # public API field name
    4: "Tattoo",    # pick a message broker
    5: "Haircut",   # pick a CSS framework
    6: "Tattoo",    # choose a license
    7: "Tattoo",    # DB engine
    8: "Hat",       # internal helper signature
}


def score_d2_classification(text: str) -> dict[str, Any]:
    """Scores response against pre-registered ground-truth labels for 8 decisions."""
    predicted = {}
    correct_count = 0

    # Search for decision labels (item 1 to 8)
    for i in range(1, 9):
        next_i = i + 1
        p_start = rf"(?:###\s*{i}\.|\bdecision\s+{i}\b|^\s*{i}\.\s+)"
        m_start = re.search(p_start, text, re.IGNORECASE | re.MULTILINE)
        if m_start:
            start_pos = m_start.end()
            if next_i <= 8:
                p_end = rf"(?:###\s*{next_i}\.|\bdecision\s+{next_i}\b|^\s*{next_i}\.\s+)"
                m_end = re.search(p_end, text[start_pos:], re.IGNORECASE | re.MULTILINE)
                target_str = text[start_pos : start_pos + m_end.start()].lower() if m_end else text[start_pos : start_pos + 600].lower()
            else:
                target_str = text[start_pos : start_pos + 600].lower()
        else:
            # Fallback to single line
            pattern = rf"(?:decision\s+{i}|{i}\.|\b{i}\b[^\n\.\:]{{0,40}}[\:\-\–])([^\n]+)"
            m = re.search(pattern, text, re.IGNORECASE)
            target_str = m.group(1).lower() if m else text.lower()

        # Determine classification
        label = "Unknown"
        m_cat = re.search(r"(?:classification|category)[\s\*\:]+([^\n\*\.]+)", target_str)
        if m_cat:
            cat_val = m_cat.group(1).lower()
            if "tattoo" in cat_val:
                label = "Tattoo"
            elif "haircut" in cat_val:
                label = "Haircut"
            elif "hat" in cat_val:
                label = "Hat"

        if label == "Unknown":
            if "tattoo" in target_str:
                label = "Tattoo"
            elif "haircut" in target_str:
                label = "Haircut"
            elif "hat" in target_str:
                label = "Hat"
            elif "reversible" in target_str and "minute" in target_str:
                label = "Hat"
            elif "irreversible" in target_str or "permanent" in target_str:
                label = "Tattoo"

        predicted[i] = label
        expected = D2_GROUND_TRUTH[i]
        if label.lower() == expected.lower():
            correct_count += 1
        elif expected == "Tattoo" and label == "Haircut" and i == 4:
            # Partial credit for message broker if argued as haircut
            correct_count += 0.5
        elif expected == "Haircut" and label == "Tattoo" and i == 2:
            # Partial credit for primary key type if argued as irreversible in prod
            correct_count += 0.5

    accuracy = round(correct_count / 8.0, 3)
    passed = accuracy >= 0.75  # Suggested pass criterion

    return {
        "accuracy": accuracy,
        "correct_count": correct_count,
        "total_items": 8,
        "predictions": predicted,
        "ground_truth": D2_GROUND_TRUTH,
        "passed": passed,
    }


# ── R1: Seeded-Flaw RFCs Ground Truth ───────────────────────────────────────

R1_PLANTED_FLAWS = {
    "RFC-1": "tattoo_disguised_as_hat",      # Public API breaking change dismissed as hat
    "RFC-2": "unbudgeted_innovation_tokens", # 3 novel tools simultaneously
    "RFC-3": "irreversible_schema_migration",# Immediate DROP TABLE without dual-writing
    "RFC-4": "mutable_status_column",       # In-place UPDATE orders SET status
    "RFC-5": "clean",                       # Read replica cache (clean)
    "RFC-6": "clean",                       # Helper refactor with unit tests (clean)
}


def score_r1_seeded_flaws(reviews: dict[str, str]) -> dict[str, Any]:
    """Computes flaw recall across 4 defective RFCs and false-positive rate across 2 clean RFCs."""
    flaw_checks = {
        "RFC-1": lambda t: bool(re.search(r"\b(tattoo|breaking|public\s+api|external\s+sdk|irreversible|not\s+a\s+hat)\b", t, re.I)),
        "RFC-2": lambda t: bool(re.search(r"\b(innovation\s+tokens?|novelty|overkill|kafka|scylla|wasm|budget)\b", t, re.I)),
        "RFC-3": lambda t: bool(re.search(r"\b(irreversible|drop\s+table|dual[- ]writ|expand[- ]contract|data\s+loss|tattoo)\b", t, re.I)),
        "RFC-4": lambda t: bool(re.search(r"\b(mutable|status\s+column|append[- ]only|ledger|in[- ]place|audit)\b", t, re.I)),
    }

    flaws_detected = 0
    details = {}

    for rfc_id, check_fn in flaw_checks.items():
        review_text = reviews.get(rfc_id, "")
        detected = check_fn(review_text)
        if detected:
            flaws_detected += 1
        details[rfc_id] = {
            "expected_flaw": R1_PLANTED_FLAWS[rfc_id],
            "detected": detected,
        }

    flaw_recall = round(flaws_detected / 4.0, 3)

    # Clean RFC false positive checks (was clean RFC flagged as flawed?)
    false_positives = 0
    clean_checks = {
        "RFC-5": lambda t: bool(re.search(r"\b(reject|critical\s+flaw|block|violation)\b", t, re.I) and not re.search(r"\b(approve|acceptable|clean|sound)\b", t, re.I)),
        "RFC-6": lambda t: bool(re.search(r"\b(reject|critical\s+flaw|block|violation)\b", t, re.I) and not re.search(r"\b(approve|acceptable|clean|sound)\b", t, re.I)),
    }

    for rfc_id, check_fn in clean_checks.items():
        review_text = reviews.get(rfc_id, "")
        is_fp = check_fn(review_text)
        if is_fp:
            false_positives += 1
        details[rfc_id] = {
            "expected": "clean",
            "falsely_flagged": is_fp,
        }

    fpr = round(false_positives / 2.0, 3)
    passed = flaw_recall >= 0.75 and fpr <= 0.15

    return {
        "flaw_recall": flaw_recall,
        "false_positive_rate": fpr,
        "flaws_detected": flaws_detected,
        "total_flaws": 4,
        "clean_rfcs_evaluated": 2,
        "false_positives": false_positives,
        "details": details,
        "passed": passed,
    }


# ── R2: PR Diff Review Ground Truth ─────────────────────────────────────────

def score_r2_pr_review(text: str) -> dict[str, Any]:
    """Verifies that PR review identifies the irreversible migration as a Tattoo and flags the dependency."""
    text_lower = text.lower()
    flags_migration_as_tattoo = bool(re.search(r"\b(tattoo|irreversible|one-way|data\s+loss)\b", text_lower))
    flags_dependency = bool(re.search(r"\b(dependency|broker|cqrs|unbudgeted|innovation\s+token)\b", text_lower))
    passed = flags_migration_as_tattoo and flags_dependency
    return {
        "flags_migration_as_tattoo": flags_migration_as_tattoo,
        "flags_dependency": flags_dependency,
        "passed": passed,
    }


# ── R3: ADR Generation and Validation ───────────────────────────────────────

def score_r3_adr(adr_text: str) -> dict[str, Any]:
    """Validates generated ADR against required sections and reversibility classification."""
    text_lower = adr_text.lower()
    has_status = bool(re.search(r"\bstatus\b[\s\*]*\:", text_lower)) or "## status" in text_lower
    has_context = "context" in text_lower
    has_decision = "decision" in text_lower
    has_consequences = "consequences" in text_lower
    classifies_tattoo = bool(re.search(r"\b(tattoo|irreversible|multi-year|high[- ]friction)\b", text_lower))

    schema_valid = has_status and has_context and has_decision and has_consequences
    passed = schema_valid and classifies_tattoo

    return {
        "schema_valid": schema_valid,
        "classifies_tattoo": classifies_tattoo,
        "has_status": has_status,
        "has_context": has_context,
        "has_decision": has_decision,
        "has_consequences": has_consequences,
        "passed": passed,
    }
