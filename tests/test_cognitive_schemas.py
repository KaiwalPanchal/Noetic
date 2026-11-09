"""Contract tests for Phase 1 Cognitive Compiler schemas and prompts.

Validates:
1. Draft-07 compliance of all schemas via Draft7Validator.check_schema().
2. Realistic valid fixtures passing Draft7 validation and internal schema_check.
3. Invalid fixtures correctly failing validation (missing fields, invalid tiers, maxLength overflow, etc.).
4. Prompt resource discovery and template variable presence.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError

from noetic.tools.schema_check import check as internal_schema_check
from noetic.orchestration.loader import find_resource


SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "workflows" / "taste_engine" / "schemas"
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "workflows" / "taste_engine" / "prompts"


def _load_schema(filename: str) -> dict:
  path = SCHEMAS_DIR / filename
  assert path.exists(), f"Schema file not found: {path}"
  return json.loads(path.read_text(encoding="utf-8"))


# --- Fixtures ---

@pytest.fixture
def extraction_schema() -> dict:
  return _load_schema("extraction.json")


@pytest.fixture
def cognitive_framework_schema() -> dict:
  return _load_schema("cognitive_framework.json")


@pytest.fixture
def synthesis_charter_schema() -> dict:
  return _load_schema("synthesis_charter.json")


@pytest.fixture
def adr_schema() -> dict:
  return _load_schema("adr.json")


@pytest.fixture
def valid_extraction_data() -> dict:
  return {
    "schema_version": "1.0.0",
    "title": "Local-First Software: You Own Your Data, in spite of the Cloud",
    "source_metadata": {
      "title": "Local-First Software",
      "author": "Martin Kleppmann et al.",
      "kind": "paper",
      "url": "https://www.inkandswitch.com/local-first/",
    },
    "entities": ["CRDT", "Local Storage", "Cloud Sync", "Multi-device", "Network Partition"],
    "core_principles": [
      {
        "name": "Local Storage as Source of Truth",
        "description": "The primary copy of every piece of data lives on the user's local device, not in the cloud.",
      },
      {
        "name": "Eventual Consistency through Math",
        "description": "Conflict-free replicated data types resolve divergent edits deterministically without centralized locks.",
      },
    ],
    "mental_moves": [
      "Store writes immediately to local SQLite or IndexedDB before attempting any network call.",
      "Treat network connections as ephemeral sync channels rather than operational prerequisites.",
      "Design data mutations as commutative operations that can be reordered safely.",
    ],
    "anti_patterns": [
      {
        "trap_name": "Cloud-First Spinner Trap",
        "symptom": "Disabling UI interactions and displaying loading spinners while waiting for a network HTTP POST.",
        "failure_mechanism": "Couples interactive UI latency directly to remote server availability and network jitter.",
        "recovery_move": "Mutate local state instantly with optimistic feedback and queue background sync.",
      }
    ],
    "genealogy": ["Git", "CouchDB", "Operational Transformation", "Marc Shapiro CRDT research"],
    "rejected": False,
    "rejection_reason": "",
    "is_signal": True,
    "signal_data": {
      "signal_summary": "Pioneering manifesto articulating the local-first engineering philosophy and CRDT primitives.",
      "noise_filtered": "Academic literature preamble and historical citations compressed.",
    },
    "harness_notes": [],
  }


@pytest.fixture
def valid_rejected_extraction_data() -> dict:
  return {
    "schema_version": "1.0.0",
    "title": "HyperScale AI Synergy 10x Paradigm",
    "source_metadata": {
      "title": "10x Synergy",
      "author": "Buzzword Influencer",
      "kind": "url",
      "url": "https://example.com/hype",
    },
    "entities": ["Synergy", "Paradigms"],
    "core_principles": [
      {
        "name": "Synergy Over All",
        "description": "Maximize vague synergy across undefined business channels.",
      }
    ],
    "mental_moves": ["Post hype on Twitter about undefined agent ecosystems."],
    "anti_patterns": [
      {
        "trap_name": "Being Slow",
        "symptom": "Not adopting trends instantly.",
        "failure_mechanism": "Missing the hype cycle.",
        "recovery_move": "Tweet more buzzwords.",
      }
    ],
    "genealogy": ["LinkedIn Thought Leaders"],
    "rejected": True,
    "rejection_reason": "Contains no executable operational primitives or falsifiable invariants; marketing hype slop.",
    "is_signal": False,
    "harness_notes": ["Source flagged as zero signal."],
  }


@pytest.fixture
def valid_framework_data() -> dict:
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
          "observable_indicator": "Read and write latency is strictly bounded by local memory and disk I/O (< 16ms).",
        },
        {
          "name": "CRDT Document",
          "kind": "entity",
          "definition": "Conflict-free replicated data structure guaranteeing strong eventual consistency.",
          "observable_indicator": "Concurrent offline edits merge deterministically without data loss or user merge prompts.",
        },
        {
          "name": "Sync Delta",
          "kind": "variable",
          "definition": "Compact operational message containing only causal mutations since the last known vector clock.",
          "observable_indicator": "WebSocket payload size scales with mutation volume, not entire document size.",
        },
      ],
      "governing_invariant": "Local Availability > Central Consensus: Local read/write operations must never block on remote network roundtrips.",
    },
    "directional_heuristics": [
      {
        "context": "When designing persistent client-side data mutations",
        "prioritize": "Immediate local persistence and optimistic UI updates",
        "over": "Blocking remote RPC mutations and loading spinners",
        "because": "Network latency and unavailability break user focus and degrade interactive fidelity.",
        "operational_rule": "Execute writes against local SQLite/IndexedDB synchronously; dispatch sync deltas asynchronously in the background.",
        "tier": 2,
        "domain_tags": ["architecture", "state-sync", "persistence"],
        "provenance_anchor": "Kleppmann Section 3: 'Data is stored on your local device... access must be fast.'",
      },
      {
        "context": "When resolving concurrent conflict across multiple devices",
        "prioritize": "Mathematical merge laws (CRDT commutativity)",
        "over": "Last-Write-Wins timestamps based on unreliable client wall clocks",
        "because": "Wall clocks drift and silently overwrite concurrent user contributions.",
        "operational_rule": "Use state-based or operation-based CRDTs with lamport timestamps and tie-breaker actor IDs.",
        "tier": 2,
        "domain_tags": ["distributed-systems", "consistency"],
        "provenance_anchor": "Kleppmann Section 4: 'CRDTs satisfy mathematical properties ensuring replicas converge.'",
      },
    ],
    "trade_off_matrix": [
      {
        "dimension": "Consistency Latency vs Storage Footprint",
        "recommended_choice": "Local storage of tombstone records and operational history",
        "sacrificed": "Minimal client storage footprint",
        "gained": "Offline usability and non-blocking real-time responsiveness",
        "boundary_flip_condition": "Client devices with severe disk constraints (< 50MB free storage) or documents with millions of historical churn events.",
      }
    ],
    "anti_patterns": [
      {
        "trap_name": "The Ephemeral Local Cache Illusion",
        "symptom": "Treating local storage as an optional cache that gets blown away on session termination.",
        "failure_mechanism": "User edits made during an offline period are wiped before syncing can occur.",
        "recovery_move": "Design local storage as the permanent primary replica with durability guarantees.",
      }
    ],
    "evaluation_rubric": {
      "the_keyboard_test": "Grepping the codebase shows zero blocking 'await fetch()' calls inside input keydown or form change handlers; all mutations write to a local db hook.",
      "admission_test_scores": {
        "executable_heuristic": 5,
        "cognitive_compression": 4,
        "keyboard_test": 5,
        "explicit_failure_mode": 4,
        "cross_domain_transfer": 4,
      },
      "falsification_criteria": "If an application requires strict linearizable total ordering with global financial atomicity (e.g. stock trading double-spend prevention), local-first CRDTs fail.",
    },
    "faithful_layer": {
      "core_idea": "Applications should give users ownership of their data by storing data primarily on local devices while preserving cross-device collaboration.",
      "razor": "If the network cable is cut, every user interaction must still succeed without error or delay.",
      "mental_moves": [
        "Invert client-server hierarchy: the cloud is an untrusted sync relay, not the brain.",
        "Model every data type as a CRDT before writing frontend components.",
        "Design for disconnected operation as the default state, connected sync as an optimization.",
      ],
    },
    "applied_layer": {
      "linked_interests": ["Local-First Architecture", "Agent Sandboxing", "High-Fidelity Interfaces"],
      "stance_alignments": ["Deterministic Control Flow", "Zero Hype Engineering"],
      "stance_conflicts": ["Centralized Cloud SaaS Lock-in"],
    },
    "genealogy": ["CouchDB", "Git Decentralized Model", "Marc Shapiro CRDTs"],
    "harness_notes": [],
  }


@pytest.fixture
def valid_synthesis_charter_data() -> dict:
  return {
    "schema_version": "1.0.0",
    "active_frameworks": ["local-first-sync", "linear-ui-speed"],
    "active_primitives": [
      {
        "name": "Local Replica",
        "framework_slug": "local-first-sync",
        "kind": "state",
        "definition": "Authoritative client database instance.",
      },
      {
        "name": "Sub-50ms Interaction Budget",
        "framework_slug": "linear-ui-speed",
        "kind": "variable",
        "definition": "Upper bound for UI feedback on any user keystroke or pointer event.",
      },
    ],
    "harmonized_heuristics": [
      {
        "framework_slug": "linear-ui-speed",
        "context": "When rendering feedback for interactive user input",
        "prioritize": "Instant visual state update (< 16ms)",
        "over": "Waiting for background validation or sync confirmation",
        "because": "Perceived speed is the dominant driver of tool mastery and user flow.",
        "operational_rule": "Update DOM/React state immediately, dispatch write transaction locally.",
        "tier": 3,
        "domain_tags": ["ui-feedback", "motion"],
        "provenance_anchor": "Linear Principle: 'Speed is a feature'",
      },
      {
        "framework_slug": "local-first-sync",
        "context": "When persisting state mutations",
        "prioritize": "Local database commit with CRDT sequence tags",
        "over": "Synchronous remote server calls",
        "because": "Prevents network partitions from breaking local task completion.",
        "operational_rule": "Commit to local SQLite before queueing sync deltas.",
        "tier": 2,
        "domain_tags": ["architecture", "persistence"],
        "provenance_anchor": "Kleppmann Section 3",
      },
    ],
    "resolved_collisions": [
      {
        "collision_dimension": "Immediate UI Feedback vs Persistence Guarantee",
        "frameworks_involved": ["linear-ui-speed", "local-first-sync"],
        "winning_framework": "local-first-sync",
        "tier_domain_rationale": "Tier 2 Architecture persistence invariant guarantees data durability before Tier 3 UI optimistic transition is confirmed.",
      }
    ],
    "unresolved_tensions": [
      {
        "tension_dimension": "Cache Truncation vs Infinite CRDT History",
        "conflicting_frameworks": ["local-first-sync", "linear-ui-speed"],
        "conflicting_heuristics": [
          "Preserve all tombstone history for offline convergence",
          "Aggressively purge local cache to maintain sub-50ms query latency",
        ],
        "escalation_note": "Same-tier memory/storage trade-off requiring human product decision on client retention window.",
      }
    ],
    "token_budget_metadata": {
      "included_count": 2,
      "trimmed_count": 4,
      "estimated_tokens": 580,
    },
    "harness_notes": [],
  }


@pytest.fixture
def valid_adr_data() -> dict:
  return {
    "schema_version": "1.0.0",
    "adr_number": "ADR-001",
    "title": "Adopt SQLite for Local-First Cache and Mutation Journal",
    "status": "pending_review",
    "target_doc": "RFC-042: Client Storage Architecture",
    "evaluated_frameworks": ["hats-haircuts-and-tattoos", "boring-technology"],
    "context_and_problem": "We need deterministic, sub-16ms query latency and offline durability without distributed locks.",
    "reversibility": {
      "classification": "haircut",
      "rationale": "Storage engine is abstracted behind repository interface; schema migrations can export to JSON.",
      "rollback_plan": "Keep legacy indexedDB adapter behind a config flag for two release cycles; failover on corruption."
    },
    "complexity_audit": {
      "tokens_spent": 1,
      "token_budget": 3,
      "rationale": "SQLite via WASM is battle-tested, consuming 1 innovation token for local file-system virtualization.",
      "simpler_alternatives": [
        "In-memory JS Map with LocalStorage fallback (insufficient query capabilities for 50k+ items)"
      ]
    },
    "framework_compliance": [
      {
        "framework": "boring-technology",
        "check_name": "Spend innovation tokens deliberately",
        "verdict": "pass",
        "critique": "SQLite is one of the most battle-tested software components in history.",
        "risk": "WASM memory growth if large blob attachments are stored directly in DB."
      },
      {
        "framework": "hats-haircuts-and-tattoos",
        "check_name": "Audit whether tattoo is disguised as haircut",
        "verdict": "pass",
        "critique": "Local storage can be rebuilt from server event stream if device is cleared.",
        "risk": "Clients with unpushed offline mutations could experience data loss during hard reset."
      }
    ],
    "unresolved_tensions": [
      {
        "tension_dimension": "Binary Size vs Query Expressiveness",
        "conflicting_frameworks": ["boring-technology", "minimal-bundle"],
        "conflicting_heuristics": ["Prefer battle-tested SQL engine", "Keep JS bundle under 100KB"],
        "escalation_note": "SQLite WASM adds ~800KB gzipped. Owner must decide if web-only users should lazy-load the storage module."
      }
    ],
    "decision_outcome": {
      "outcome": "compromise",
      "justification": "Adopt SQLite WASM for desktop and rich web client, with lazy loading on mobile web.",
      "consequences": "Sub-10ms queries achieved. Increased initial download by 800KB for rich client sessions."
    },
    "provenance": "Generated by Mode B sparring pipeline (spar) run 20261109-1400 on 2026-11-09."
  }


# --- Draft-07 Meta-Schema Tests ---

def test_extraction_schema_valid_draft07(extraction_schema):
  """Verify extraction.json is valid Draft-07 JSON Schema."""
  Draft7Validator.check_schema(extraction_schema)
  assert extraction_schema.get("$schema") == "http://json-schema.org/draft-07/schema#"


def test_cognitive_framework_schema_valid_draft07(cognitive_framework_schema):
  """Verify cognitive_framework.json is valid Draft-07 JSON Schema."""
  Draft7Validator.check_schema(cognitive_framework_schema)
  assert cognitive_framework_schema.get("$schema") == "http://json-schema.org/draft-07/schema#"


def test_synthesis_charter_schema_valid_draft07(synthesis_charter_schema):
  """Verify synthesis_charter.json is valid Draft-07 JSON Schema."""
  Draft7Validator.check_schema(synthesis_charter_schema)
  assert synthesis_charter_schema.get("$schema") == "http://json-schema.org/draft-07/schema#"


def test_adr_schema_valid_draft07(adr_schema):
  """Verify adr.json is valid Draft-07 JSON Schema [Phase 4, R1]."""
  Draft7Validator.check_schema(adr_schema)
  assert adr_schema.get("$schema") == "http://json-schema.org/draft-07/schema#"


# --- Mandatory schema_version [P0.1, R1] Tests ---

@pytest.mark.parametrize("schema_name", ["extraction.json", "cognitive_framework.json", "synthesis_charter.json", "adr.json"])
def test_schema_version_is_mandatory(schema_name):
  schema = _load_schema(schema_name)
  assert "schema_version" in schema.get("properties", {})
  assert "schema_version" in schema.get("required", [])
  sv = schema["properties"]["schema_version"]
  assert sv.get("const") == "1.0.0" or sv.get("enum") == ["1.0.0"]


# --- Valid Fixture Validation Tests ---

def test_valid_extraction_fixture(extraction_schema, valid_extraction_data):
  """Extraction fixture passes Draft7Validator and internal schema_check."""
  validator = Draft7Validator(extraction_schema)
  validator.validate(valid_extraction_data)
  errors = internal_schema_check(valid_extraction_data, extraction_schema)
  assert errors == []


def test_valid_rejected_extraction_fixture(extraction_schema, valid_rejected_extraction_data):
  """Rejected extraction fixture passes validation."""
  validator = Draft7Validator(extraction_schema)
  validator.validate(valid_rejected_extraction_data)
  errors = internal_schema_check(valid_rejected_extraction_data, extraction_schema)
  assert errors == []


def test_valid_cognitive_framework_fixture(cognitive_framework_schema, valid_framework_data):
  """Cognitive framework fixture passes Draft7Validator and internal schema_check."""
  validator = Draft7Validator(cognitive_framework_schema)
  validator.validate(valid_framework_data)
  errors = internal_schema_check(valid_framework_data, cognitive_framework_schema)
  assert errors == []


def test_valid_synthesis_charter_fixture(synthesis_charter_schema, valid_synthesis_charter_data):
  """Synthesis charter fixture passes Draft7Validator and internal schema_check."""
  validator = Draft7Validator(synthesis_charter_schema)
  validator.validate(valid_synthesis_charter_data)
  errors = internal_schema_check(valid_synthesis_charter_data, synthesis_charter_schema)
  assert errors == []


def test_valid_adr_fixture(adr_schema, valid_adr_data):
  """ADR fixture passes Draft7Validator and internal schema_check [Phase 4, R1+R2]."""
  validator = Draft7Validator(adr_schema)
  validator.validate(valid_adr_data)
  errors = internal_schema_check(valid_adr_data, adr_schema)
  assert errors == []


# --- Invalid Fixtures: extraction.json ---

def test_extraction_missing_schema_version_fails(extraction_schema, valid_extraction_data):
  data = dict(valid_extraction_data)
  del data["schema_version"]
  validator = Draft7Validator(extraction_schema)
  with pytest.raises(ValidationError) as exc:
    validator.validate(data)
  assert "schema_version" in str(exc.value)


def test_extraction_invalid_schema_version_fails(extraction_schema, valid_extraction_data):
  data = dict(valid_extraction_data)
  data["schema_version"] = "2.0.0"
  validator = Draft7Validator(extraction_schema)
  with pytest.raises(ValidationError):
    validator.validate(data)


def test_extraction_title_max_length_fails(extraction_schema, valid_extraction_data):
  data = dict(valid_extraction_data)
  data["title"] = "X" * 301
  validator = Draft7Validator(extraction_schema)
  with pytest.raises(ValidationError) as exc:
    validator.validate(data)
  assert "maxLength" in str(exc.value) or "301" in str(exc.value)


def test_extraction_invalid_source_kind_fails(extraction_schema, valid_extraction_data):
  data = dict(valid_extraction_data)
  data["source_metadata"] = dict(data["source_metadata"])
  data["source_metadata"]["kind"] = "unsupported_kind"
  validator = Draft7Validator(extraction_schema)
  with pytest.raises(ValidationError):
    validator.validate(data)


def test_extraction_missing_required_rejected_flag(extraction_schema, valid_extraction_data):
  data = dict(valid_extraction_data)
  del data["rejected"]
  validator = Draft7Validator(extraction_schema)
  with pytest.raises(ValidationError):
    validator.validate(data)


# --- Invalid Fixtures: cognitive_framework.json ---

def test_cognitive_framework_missing_tier_fails(cognitive_framework_schema, valid_framework_data):
  data = json.loads(json.dumps(valid_framework_data))
  del data["directional_heuristics"][0]["tier"]
  validator = Draft7Validator(cognitive_framework_schema)
  with pytest.raises(ValidationError) as exc:
    validator.validate(data)
  assert "tier" in str(exc.value)


@pytest.mark.parametrize("invalid_tier", [0, 5, -1, 10, "2"])
def test_cognitive_framework_invalid_tier_fails(cognitive_framework_schema, valid_framework_data, invalid_tier):
  data = json.loads(json.dumps(valid_framework_data))
  data["directional_heuristics"][0]["tier"] = invalid_tier
  validator = Draft7Validator(cognitive_framework_schema)
  with pytest.raises(ValidationError):
    validator.validate(data)


def test_cognitive_framework_missing_provenance_anchor_fails(cognitive_framework_schema, valid_framework_data):
  data = json.loads(json.dumps(valid_framework_data))
  del data["directional_heuristics"][0]["provenance_anchor"]
  validator = Draft7Validator(cognitive_framework_schema)
  with pytest.raises(ValidationError) as exc:
    validator.validate(data)
  assert "provenance_anchor" in str(exc.value)


def test_cognitive_framework_missing_faithful_layer_fails(cognitive_framework_schema, valid_framework_data):
  data = json.loads(json.dumps(valid_framework_data))
  del data["faithful_layer"]
  validator = Draft7Validator(cognitive_framework_schema)
  with pytest.raises(ValidationError) as exc:
    validator.validate(data)
  assert "faithful_layer" in str(exc.value)


def test_cognitive_framework_missing_applied_layer_fails(cognitive_framework_schema, valid_framework_data):
  data = json.loads(json.dumps(valid_framework_data))
  del data["applied_layer"]
  validator = Draft7Validator(cognitive_framework_schema)
  with pytest.raises(ValidationError) as exc:
    validator.validate(data)
  assert "applied_layer" in str(exc.value)


def test_cognitive_framework_invalid_primitive_kind_fails(cognitive_framework_schema, valid_framework_data):
  data = json.loads(json.dumps(valid_framework_data))
  data["ontology"]["primitives"][0]["kind"] = "magic_power"
  validator = Draft7Validator(cognitive_framework_schema)
  with pytest.raises(ValidationError):
    validator.validate(data)


def test_cognitive_framework_invalid_admission_score_fails(cognitive_framework_schema, valid_framework_data):
  data = json.loads(json.dumps(valid_framework_data))
  data["evaluation_rubric"]["admission_test_scores"]["executable_heuristic"] = 6
  validator = Draft7Validator(cognitive_framework_schema)
  with pytest.raises(ValidationError):
    validator.validate(data)


def test_cognitive_framework_string_exceeding_max_length_fails(cognitive_framework_schema, valid_framework_data):
  data = json.loads(json.dumps(valid_framework_data))
  data["framework_name"] = "A" * 201
  validator = Draft7Validator(cognitive_framework_schema)
  with pytest.raises(ValidationError):
    validator.validate(data)


def test_cognitive_framework_slug_pattern_fails(cognitive_framework_schema, valid_framework_data):
  data = json.loads(json.dumps(valid_framework_data))
  data["slug"] = "Invalid Slug With Spaces"
  validator = Draft7Validator(cognitive_framework_schema)
  with pytest.raises(ValidationError):
    validator.validate(data)


# --- Invalid Fixtures: synthesis_charter.json ---

def test_synthesis_charter_missing_token_budget_metadata(synthesis_charter_schema, valid_synthesis_charter_data):
  data = json.loads(json.dumps(valid_synthesis_charter_data))
  del data["token_budget_metadata"]
  validator = Draft7Validator(synthesis_charter_schema)
  with pytest.raises(ValidationError) as exc:
    validator.validate(data)
  assert "token_budget_metadata" in str(exc.value)


def test_synthesis_charter_negative_token_count_fails(synthesis_charter_schema, valid_synthesis_charter_data):
  data = json.loads(json.dumps(valid_synthesis_charter_data))
  data["token_budget_metadata"]["included_count"] = -1
  validator = Draft7Validator(synthesis_charter_schema)
  with pytest.raises(ValidationError):
    validator.validate(data)


def test_synthesis_charter_empty_active_frameworks_fails(synthesis_charter_schema, valid_synthesis_charter_data):
  data = json.loads(json.dumps(valid_synthesis_charter_data))
  data["active_frameworks"] = []
  validator = Draft7Validator(synthesis_charter_schema)
  with pytest.raises(ValidationError):
    validator.validate(data)


def test_synthesis_charter_missing_unresolved_tensions_fails(synthesis_charter_schema, valid_synthesis_charter_data):
  data = json.loads(json.dumps(valid_synthesis_charter_data))
  del data["unresolved_tensions"]
  validator = Draft7Validator(synthesis_charter_schema)
  with pytest.raises(ValidationError):
    validator.validate(data)


# --- Prompt Files Existence and Content Tests ---

@pytest.mark.parametrize("prompt_name", ["extract.md", "build_framework.md", "synthesize.md", "spar.md"])
def test_prompt_files_exist(prompt_name):
  prompt_path = PROMPTS_DIR / prompt_name
  assert prompt_path.exists(), f"Prompt file missing: {prompt_path}"
  content = prompt_path.read_text(encoding="utf-8")
  assert len(content) > 100
  assert "{{preamble}}" in content


def test_extract_prompt_defense_instructions():
  content = (PROMPTS_DIR / "extract.md").read_text(encoding="utf-8")
  assert "Zero Tool Access" in content or "zero tool" in content.lower()
  assert "rejected" in content
  assert "injection" in content.lower()


def test_build_framework_prompt_5_blocks():
  content = (PROMPTS_DIR / "build_framework.md").read_text(encoding="utf-8")
  assert "Ontology" in content
  assert "Directional Heuristics" in content
  assert "Trade-Off Matrix" in content
  assert "Anti-Patterns" in content
  assert "Evaluation Rubric" in content
  assert "faithful_layer" in content
  assert "applied_layer" in content


def test_synthesize_prompt_tier_and_tension_rules():
  content = (PROMPTS_DIR / "synthesize.md").read_text(encoding="utf-8")
  assert "Tier 1" in content
  assert "Tier 2" in content
  assert "Tier 3" in content
  assert "Tier 4" in content
  assert "unresolved_tensions" in content
  assert "resolved_collisions" in content


def test_spar_prompt_reversibility_and_token_rules():
  content = (PROMPTS_DIR / "spar.md").read_text(encoding="utf-8")
  assert "Hats, Haircuts, and Tattoos" in content
  assert "Boring Technology" in content
  assert "hat" in content.lower()
  assert "haircut" in content.lower()
  assert "tattoo" in content.lower()
  assert "innovation tokens" in content.lower()
  assert "rollback_plan" in content
  assert "adr.json" in content
