"""Deterministic Scorers (DET) for Behavioral Verification Plan.

Implements Section 5 deterministic code, AST, and structural invariant checks.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re
from typing import Any

from noetic.gates.policy_gate import SecurityViolation, sanitize_input
from noetic.knowledge.stack import check_framework_trust


def extract_python_code(text: str) -> str:
    """Extracts Python code blocks from markdown text."""
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)\n```", text, re.DOTALL)
    if blocks:
        return "\n\n".join(blocks)
    # If no fences, attempt to find def/class
    m = re.search(r"((?:class|def)\s+[a-zA-Z0-9_]+.*)", text, re.DOTALL)
    return m.group(1) if m else text


# ── D1: Count New Technologies Adopted (DET: count <= 2) ────────────────────

def score_d1_tech_count(text: str) -> dict[str, Any]:
    """Counts new technologies adopted (budget <= 2 innovation tokens)."""
    text_lower = text.lower()
    novel_candidates = ["kafka", "event sourcing", "graph database", "neo4j"]
    adopted = []
    rejected = []

    # Common rejection phrases in tech evaluations
    rejection_pattern = re.compile(
        r"\b(reject(?:ed|ing|s)?|avoid(?:ed|ing|s)?|unnecessary|not recommended|drop(?:ped)?|skip(?:ped)?|overkill|stick to|do not use|without|"
        r"should not be accepted|decline|postpone|revisit .* only|consume .* tokens|do not adopt|do not introduce)\b",
        re.I,
    )

    for tech in novel_candidates:
        if tech in text_lower:
            # Check context window (150 chars around each mention)
            is_rejected = False
            for m in re.finditer(re.escape(tech), text_lower):
                start = max(0, m.start() - 150)
                end = min(len(text_lower), m.end() + 150)
                window = text_lower[start:end]
                if rejection_pattern.search(window):
                    is_rejected = True
                    break
            if is_rejected:
                rejected.append(tech)
            else:
                adopted.append(tech)

    recommends_postgres_django = bool(re.search(r"\b(postgres|django|postgresql)\b", text_lower))
    token_budget_mentioned = bool(re.search(r"\b(innovation tokens?|novelty budget|tokens?)\b", text_lower))

    # The adopted technologies are only those not rejected
    new_tech_count = len(adopted)
    passed = new_tech_count <= 2 and recommends_postgres_django

    return {
        "new_tech_count": new_tech_count,
        "adopted_technologies": adopted,
        "rejected_technologies": rejected,
        "recommends_postgres_django": recommends_postgres_django,
        "token_budget_mentioned": token_budget_mentioned,
        "passed": passed,
    }


# ── D4: Deep Modules Public Interface (DET: public methods <= 5) ─────────────

def score_d4_interface_depth(text: str) -> dict[str, Any]:
    """Analyzes AST of client class; counts public methods and parameters."""
    code = extract_python_code(text)
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Fallback to regex counting of def statements
        methods = re.findall(r"def\s+([a-zA-Z0-9_]+)\s*\((.*?)\)", code)
        public = [m for m, p in methods if not m.startswith("_")]
        count = len(public) if public else 6
        return {
            "public_methods_count": count,
            "avg_parameters": 2.0,
            "is_deep": count <= 5,
            "passed": count <= 5,
            "syntax_valid": False,
        }

    public_methods = []
    param_counts = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                public_methods.append(node.name)
                # Count non-self parameters
                args = [a.arg for a in node.args.args if a.arg != "self"]
                param_counts.append(len(args))

    count = len(public_methods)
    avg_params = (sum(param_counts) / len(param_counts)) if param_counts else 0.0
    is_deep = 1 <= count <= 5 and avg_params <= 3.5

    return {
        "public_methods_count": count,
        "public_methods": public_methods,
        "avg_parameters": round(avg_params, 2),
        "is_deep": is_deep,
        "passed": is_deep,
        "syntax_valid": True,
    }


# ── D5: Canary Ledger Request Handler (DET: AST and Grep) ───────────────────

def score_d5_canary_ledger(text: str) -> dict[str, Any]:
    """Validates the two canary rules:

    Rule 1: State modeled as append-only ledger tables (no mutable status column updates).
    Rule 2: Handlers nest at most 2 levels; 3rd level extracted into named step_ helper.
    """
    code = extract_python_code(text)
    text_lower = text.lower()

    # Rule 1 Check:
    # Fail if code contains in-place UPDATE orders SET status or mutable assignment to order.status
    has_mutable_sql = bool(re.search(r"update\s+orders?\s+set\s+status\s*=", text_lower))
    has_mutable_attr = bool(re.search(r"order\.status\s*=", text_lower))
    has_append_only_event = bool(re.search(r"(order_events|ledger|transitions|insert\s+into\s+[a-z_]+_events)", text_lower))

    rule1_passed = (not has_mutable_sql) and (not has_mutable_attr) and has_append_only_event

    # Rule 2 Check via AST:
    rule2_passed = False
    max_nesting_depth = 0
    has_step_function = False
    step_functions_found = []

    try:
        tree = ast.parse(code)

        # Look for functions starting with step_
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("step_"):
                    has_step_function = True
                    step_functions_found.append(node.name)

        # Measure block nesting depth inside handler functions
        def get_max_depth(node: ast.AST, current_depth: int = 0) -> int:
            depths = [current_depth]
            nesting_constructs = (
                ast.If, ast.For, ast.While, ast.With, ast.AsyncWith,
                ast.Try, ast.ExceptHandler,
            )
            for child in ast.iter_child_nodes(node):
                if isinstance(child, nesting_constructs):
                    depths.append(get_max_depth(child, current_depth + 1))
                else:
                    depths.append(get_max_depth(child, current_depth))
            return max(depths)

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("step_"):
                    # This is the main handler
                    d = get_max_depth(node, current_depth=0)
                    if d > max_nesting_depth:
                        max_nesting_depth = d

        # Nesting budget: at most 2 levels inside handler body
        rule2_passed = (max_nesting_depth <= 2) and has_step_function

    except SyntaxError:
        # Fallback inspection if snippet has formatting markers
        has_step_function = bool(re.search(r"\bdef\s+step_[a-zA-Z0-9_]+", text))
        rule2_passed = has_step_function

    overall_passed = rule1_passed and rule2_passed

    return {
        "rule1_append_only": rule1_passed,
        "rule1_details": {
            "no_mutable_sql": not has_mutable_sql,
            "no_mutable_attr": not has_mutable_attr,
            "has_append_only_event": has_append_only_event,
        },
        "rule2_nesting_limit": rule2_passed,
        "rule2_details": {
            "max_nesting_depth": max_nesting_depth,
            "has_step_function": has_step_function,
            "step_functions": step_functions_found,
        },
        "canary_passed": overall_passed,
        "passed": overall_passed,
    }


# ── S1: Stacking & Collision (DET: synthesis charter schema & unresolved_tensions) ─

def score_s1_collision_charter(charter_dict: dict[str, Any]) -> dict[str, Any]:
    """Validates synthesis charter contains unresolved tensions for conflicting same-tier frameworks."""
    import jsonschema
    schema_file = Path(__file__).resolve().parents[4] / "workflows" / "taste_engine" / "schemas" / "synthesis_charter.json"
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(instance=charter_dict, schema=schema)
        schema_valid = True
    except Exception:
        schema_valid = False

    tensions = charter_dict.get("unresolved_tensions", [])
    has_tension = len(tensions) >= 1

    # Verify both deep-modules and small-functions mentioned
    tension_text = json.dumps(tensions).lower()
    mentions_both = ("deep-modules" in tension_text or "interface" in tension_text or "consolidated" in tension_text) and (
        "small-functions" in tension_text or "decomposition" in tension_text or "line" in tension_text or "tiny" in tension_text
    )

    passed = schema_valid and has_tension and mentions_both
    return {
        "schema_valid": schema_valid,
        "has_unresolved_tensions": has_tension,
        "tensions_count": len(tensions),
        "mentions_both_frameworks": mentions_both,
        "passed": passed,
    }


# ── S2: Cross-Tier Collision (DET: Tier 1 canary-ledger wins over Tier 2) ─────

def score_s2_tier_hierarchy(charter_dict: dict[str, Any]) -> dict[str, Any]:
    """Verifies that Tier 1 rules triumph over Tier 2 rules in resolved_collisions."""
    collisions = charter_dict.get("resolved_collisions", [])
    has_collision = len(collisions) >= 1
    tier1_won = False

    for c in collisions:
        winner = c.get("winning_framework", "")
        rationale = str(c.get("tier_domain_rationale", "")).lower()
        if winner == "canary-ledger" or "tier 1" in rationale:
            tier1_won = True
            break

    passed = has_collision and tier1_won
    return {
        "has_resolved_collisions": has_collision,
        "tier1_won": tier1_won,
        "passed": passed,
    }


# ── N4: Output Overhead on Trivial Task (DET: length ratio <= 1.2x) ───────────

def score_n4_overhead(c3_text: str, c0_text: str) -> dict[str, Any]:
    """Checks output word count ratio between C3 and C0 on trivial variable rename."""
    c0_words = len(c0_text.split())
    c3_words = len(c3_text.split())
    ratio = round(c3_words / max(1, c0_words), 2)
    passed = ratio <= 1.20
    return {
        "c0_word_count": c0_words,
        "c3_word_count": c3_words,
        "length_ratio": ratio,
        "passed": passed,
    }


# ── X1: Security Check: Unapproved & Tampered Note Serving ───────────────────

def score_x1_security_mcp_trust(vault_dir: Path) -> dict[str, Any]:
    """Verifies MCP server blocks pending_review note and hash-mismatched note."""
    fw_dir = vault_dir / "frameworks"
    unapproved_path = fw_dir / "unapproved-test-note.md"
    tampered_path = fw_dir / "tampered-test-note.md"

    # 1. Create an unapproved note
    unapproved_path.write_text(
        "---\nauthor: test\nstatus: pending_review\n---\n# Framework: Unapproved\n",
        encoding="utf-8",
    )
    ok_unapproved, err_unapproved = check_framework_trust(unapproved_path, include_unapproved=False, verify_hash=True)

    # 2. Create an approved note, then tamper with its text
    tampered_path.write_text(
        "---\nauthor: test\nstatus: approved\napproval_hash: \"1111111111111111111111111111111111111111111111111111111111111111\"\n---\n# Framework: Tampered Note\n",
        encoding="utf-8",
    )
    ok_tampered, err_tampered = check_framework_trust(tampered_path, include_unapproved=False, verify_hash=True)

    # Clean up test notes
    unapproved_path.unlink(missing_ok=True)
    tampered_path.unlink(missing_ok=True)

    unapproved_blocked = not ok_unapproved
    tampered_blocked = (not ok_tampered) and ("HASH_MISMATCH" in err_tampered or "not approved" in err_tampered)
    passed = unapproved_blocked and tampered_blocked

    return {
        "unapproved_blocked": unapproved_blocked,
        "tampered_blocked": tampered_blocked,
        "err_unapproved": err_unapproved,
        "err_tampered": err_tampered,
        "passed": passed,
    }
