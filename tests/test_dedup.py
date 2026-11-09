"""Tests for knowledge deduplication and embedding graph intelligence.

Tests:
1. Core semantic text extraction (ontology entities, directional heuristics, trade-off matrix) [R2]
2. SQLite embedding cache (.noetic/embeddings.db) with SHA-256 cache key [R1+R2]
3. Tier 1 slug matching and length/slug guards [R1]
4. Threshold calibration across labeled dataset pairs [R1]
5. 3-tier deduplication actions: MERGE, COUSIN, CREATE
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3

import pytest

from noetic.knowledge.config import Config
from noetic.knowledge.dedup import (
    CALIBRATION_DATASET,
    SHORT_SLUG_GUARDS,
    calibrate_thresholds,
    core_semantic_text,
    cosine_similarity,
    deduplicate_framework,
    deterministic_vector,
    get_embedding,
    get_embedding_db_path,
    make_cache_key,
)


@pytest.fixture
def cognitive_fixture() -> dict:
    return {
        "schema_version": "1.0.0",
        "framework_name": "Local-First Sync Architecture",
        "slug": "local-first-sync",
        "source": {
            "title": "Local-First Software",
            "author": "Martin Kleppmann et al.",
            "kind": "paper",
            "url": "https://www.inkandswitch.com/local-first/",
        },
        "ontology": {
            "domain": "Distributed Systems & UI State",
            "primitives": [
                {
                    "name": "Local State",
                    "kind": "state",
                    "definition": "The authoritative client-side replica persisting user mutations without network dependency.",
                    "observable_indicator": "Read and write latency bounded by disk I/O.",
                },
                {
                    "name": "CRDT Document",
                    "kind": "entity",
                    "definition": "Conflict-free replicated data structure guaranteeing eventual consistency.",
                    "observable_indicator": "Concurrent edits merge deterministically.",
                },
            ],
            "governing_invariant": "Local Availability > Central Consensus.",
        },
        "directional_heuristics": [
            {
                "context": "When designing persistent client-side mutations",
                "prioritize": "Immediate local persistence and optimistic UI updates",
                "over": "Blocking remote RPC mutations and loading spinners",
                "because": "Network latency breaks user focus.",
                "operational_rule": "Execute writes against local SQLite synchronously; sync asynchronously.",
                "tier": 2,
                "domain_tags": ["architecture", "persistence"],
                "provenance_anchor": "Kleppmann Section 3.",
            }
        ],
        "trade_off_matrix": [
            {
                "dimension": "Consistency Latency vs Storage Footprint",
                "recommended_choice": "Local storage of tombstone records",
                "sacrificed": "Minimal client storage footprint",
                "gained": "Offline usability and non-blocking real-time responsiveness",
                "boundary_flip_condition": "Client devices with severe disk constraints (< 50MB free storage).",
            }
        ],
        "anti_patterns": [
            {
                "trap_name": "Ephemeral Local Cache",
                "symptom": "Treating local storage as an optional cache.",
                "failure_mechanism": "Offline edits wiped before sync.",
                "recovery_move": "Design local storage as permanent primary replica.",
            }
        ],
        "evaluation_rubric": {
            "the_keyboard_test": "Grepping shows zero blocking fetch calls in UI handlers.",
            "admission_test_scores": {
                "executable_heuristic": 5,
                "cognitive_compression": 5,
                "keyboard_test": 5,
                "explicit_failure_mode": 4,
                "cross_domain_transfer": 4,
            },
            "falsification_criteria": "If app requires global total order financial locking, CRDT fails.",
        },
        "faithful_layer": {
            "core_idea": "Applications should give users ownership of their data by storing data locally.",
            "razor": "If the network cable is cut, every user interaction must still succeed.",
            "mental_moves": ["Invert client-server hierarchy", "Model data as CRDT"],
        },
        "applied_layer": {
            "linked_interests": ["Local-First Architecture"],
            "stance_alignments": ["Deterministic Control Flow"],
            "stance_conflicts": ["Centralized Cloud SaaS Lock-in"],
        },
        "genealogy": ["Git", "Marc Shapiro CRDTs"],
    }


def test_core_semantic_text_extracts_only_core_fields(cognitive_fixture):
    text = core_semantic_text(cognitive_fixture)
    assert "entity: Local State" in text
    assert "entity: CRDT Document" in text
    assert "invariant: Local Availability > Central Consensus." in text
    assert "heuristic: in When designing persistent client-side mutations prioritize" in text
    assert "trade-off: Consistency Latency vs Storage Footprint: recommend Local storage" in text
    # Narrative/eval/source metadata should NOT be in the core semantic text
    assert "Martin Kleppmann" not in text
    assert "https://www.inkandswitch.com" not in text
    assert "the_keyboard_test" not in text
    assert "Deterministic Control Flow" not in text


def test_core_semantic_text_legacy_fallback():
    legacy = {
        "framework_name": "Steal Like An Artist",
        "slug": "steal-like-an-artist",
        "core_idea": "Nothing is original; remix with credit.",
        "principles": [
            {"name": "Steal", "explanation": "Collect influences."},
            {"name": "Transform", "explanation": "Make it yours."},
        ],
        "mental_moves": ["collect", "remix", "credit"],
    }
    text = core_semantic_text(legacy)
    assert "principle: Steal: Collect influences." in text
    assert "move: collect" in text
    assert "core: Nothing is original; remix with credit." in text


def test_make_cache_key_sha256_format():
    key = make_cache_key("test text", "openai", "text-embedding-3-small", "1")
    assert len(key) == 64
    expected = hashlib.sha256(b"test text:openai:text-embedding-3-small:1").hexdigest()
    assert key == expected


def test_embedding_cache_sqlite_lifecycle(cfg, cognitive_fixture):
    db_path = get_embedding_db_path(cfg)
    assert not db_path.exists()

    text = core_semantic_text(cognitive_fixture)
    vec1 = get_embedding(text, cfg)
    assert db_path.exists()
    assert len(vec1) > 0

    # Verify stored in SQLite
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT cache_key, vector, provider, model, version FROM embeddings")
    rows = cursor.fetchall()
    conn.close()
    assert len(rows) == 1
    stored_key, stored_vec_json, prov, model, ver = rows[0]
    assert stored_key == make_cache_key(text, cfg.embedding_model["provider"], cfg.embedding_model["model"], cfg.embedding_model["version"])
    assert json.loads(stored_vec_json) == vec1

    # Second fetch reuses cache
    vec2 = get_embedding(text, cfg)
    assert vec1 == vec2


def test_cosine_similarity_properties():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    v_zero = [0.0, 0.0, 0.0]

    assert pytest.approx(cosine_similarity(v1, v2), 0.001) == 1.0
    assert pytest.approx(cosine_similarity(v1, v3), 0.001) == 0.0
    assert cosine_similarity(v1, v_zero) == 0.0
    assert cosine_similarity([], v1) == 0.0


def test_threshold_calibration_dataset_guarantees():
    results = calibrate_thresholds(deterministic_vector)
    
    # 1. Identical pairs must score >= 0.85
    for score in results["identical"]:
        assert score >= 0.85, f"Identical pair score {score} failed threshold >= 0.85"

    # 2. Cousin pairs must score >= 0.65 and < 0.85
    for score in results["cousin"]:
        assert 0.65 <= score < 0.85, f"Cousin pair score {score} outside threshold [0.65, 0.85)"

    # 3. Unrelated pairs must score < 0.65
    for score in results["unrelated"]:
        assert score < 0.65, f"Unrelated pair score {score} failed threshold < 0.65"


def test_slug_guards_prevent_false_merges_on_short_slugs(cfg, cognitive_fixture):
    # Pre-create a framework note with short slug "ui.md"
    ui_note = cfg.frameworks / "ui.md"
    ui_note.write_text("""---
author: test-author
status: approved
type: framework
---
# Framework: UI Primitives
<!-- NOETIC:AUTO:START -->
entity: UI Button
<!-- NOETIC:AUTO:END -->
""", encoding="utf-8")

    # Candidate with short slug "ui"
    candidate = dict(cognitive_fixture)
    candidate["slug"] = "ui"
    candidate["framework_name"] = "UI Framework"

    # Must NOT trigger Tier 1 MERGE on "ui"
    res = deduplicate_framework(cfg, candidate)
    assert res["action"] != "MERGE" or "Tier 1" not in res["reason"]

    # Candidate with guarded slug "c4"
    c4_note = cfg.frameworks / "c4.md"
    c4_note.write_text("# Framework: C4 Architecture\n", encoding="utf-8")
    candidate["slug"] = "c4"
    res_c4 = deduplicate_framework(cfg, candidate)
    assert res_c4["action"] != "MERGE" or "Tier 1" not in res_c4["reason"]


def test_tier_1_exact_slug_match(cfg, cognitive_fixture):
    existing = cfg.frameworks / "local-first-sync.md"
    existing.write_text("# Framework: Local First Sync\n", encoding="utf-8")

    res = deduplicate_framework(cfg, cognitive_fixture)
    assert res["action"] == "MERGE"
    assert res["target_path"] == existing
    assert res["target_slug"] == "local-first-sync"
    assert "Tier 1" in res["reason"]


def test_tier_2_identical_embedding_match(cfg, cognitive_fixture):
    # Create note with identical semantic text but DIFFERENT slug
    existing = cfg.frameworks / "offline-local-storage.md"
    existing.write_text(f"""---
status: approved
---
<!-- NOETIC:AUTO:START -->
# Framework: Offline Local Storage
{core_semantic_text(cognitive_fixture)}
<!-- NOETIC:AUTO:END -->
""", encoding="utf-8")

    candidate = dict(cognitive_fixture)
    candidate["slug"] = "novel-sounding-local-sync"

    res = deduplicate_framework(cfg, candidate)
    assert res["action"] == "MERGE"
    assert res["target_path"] == existing
    assert "Tier 2" in res["reason"]
    assert res["score"] >= 0.85


def test_tier_2_cousin_embedding_match(cfg):
    pair_a, pair_b = CALIBRATION_DATASET["cousin"][0]
    existing = cfg.frameworks / "decision-reversibility-taxonomy.md"
    existing.write_text(f"""---
status: approved
---
<!-- NOETIC:AUTO:START -->
# Framework: Decision Reversibility Taxonomy
{pair_a}
<!-- NOETIC:AUTO:END -->
""", encoding="utf-8")

    candidate = {
        "framework_name": "Executive Two-Way Doors",
        "slug": "executive-two-way-doors",
        "ontology": {"primitives": [{"name": "Two-Way Door", "kind": "entity", "definition": "Reversibility taxonomy and delegation", "observable_indicator": "Speed"}], "governing_invariant": "Speed on reversible calls"},
        "directional_heuristics": [
            {
                "context": "When evaluating organizational choices",
                "prioritize": "delegating two-way door decisions",
                "over": "executive deliberation because two-way doors are easily reversible",
                "because": "speed on reversible decisions",
                "operational_rule": "push reversible decisions down",
                "tier": 4,
                "domain_tags": ["governance"],
                "provenance_anchor": "Bezos Letter",
            }
        ],
        "trade_off_matrix": [
            {
                "dimension": "Speed vs executive control",
                "recommended_choice": "speed on reversible decisions",
                "sacrificed": "management oversight",
                "gained": "organizational velocity",
                "boundary_flip_condition": "irreversible one-way door choices",
            }
        ],
    }

    res = deduplicate_framework(cfg, candidate)
    assert res["action"] == "COUSIN"
    assert res["target_path"] == existing
    assert 0.65 <= res["score"] < 0.85


def test_tier_3_novel_framework_creation(cfg, cognitive_fixture):
    # Empty vault -> novel framework
    res = deduplicate_framework(cfg, cognitive_fixture)
    assert res["action"] == "CREATE"
    assert res["target_path"] is None
    assert "Tier 3" in res["reason"]
