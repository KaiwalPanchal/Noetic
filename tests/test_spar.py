"""Tests for Mode B Sparring & ADR Engine in taste_engine.pipelines.spar [Phase 4, R1+R2].

Validates:
1. Config-driven lenses: reads default_lenses from noetic.config.json (zero hardcoded Python cognitive logic) [R2]
2. Loud failure on missing, unapproved, or tampered lenses (PipelineError("LENS_UNAVAILABLE")) [R1+R2]
3. Standardized synthesis_charter.json consumption [R2]
4. Concurrency-safe atomic ADR numbering via directory lockfile [R1]
5. ADR note creation with status: pending_review and lifecycle transition to accepted via gate.approve() [R1]
6. Human edits outside <!-- NOETIC:AUTO:START/END --> preserved across updates [R1+R2]
7. Framework note Applications Log appended strictly inside <!-- NOETIC:LOG:START/END --> without touching human content [R2]
"""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import pytest

from noetic.agents.runners import AgentResult
from noetic.gates import gate
from noetic.knowledge import notes
from noetic.knowledge.config import CONFIG_NAME, Config, today
from noetic.knowledge.notes import AUTO_END, AUTO_START, LOG_END, LOG_START, set_status
from noetic.orchestration.run import PipelineError, Run
import noetic.orchestration.steps as steps_mod
from workflows.taste_engine.pipelines.spar import (
    dir_lock,
    next_atomic_adr_number,
    reserve_next_adr_number,
    resolve_adr_dir,
    resolve_framework_path,
    spar,
)


def _make_lens(
    vault: Path,
    slug: str,
    title: str,
    tier: int = 1,
    domain: str = "governance",
    status: str = "approved",
    extra_human_text: str = "",
) -> Path:
  fw_file = vault / "frameworks" / f"{slug}.md"
  fw_file.parent.mkdir(parents=True, exist_ok=True)

  content = f"""---
author: ai-agent
status: pending_review
schema_version: 1.0.0
---
<!-- NOETIC:AUTO:START -->
# Framework: {title}

**Source:** {title} Primary Source  
**Tags:** #framework #{domain}  
**Admission Score:** 5.0/5.0  
**The Keyboard Test:** Automated test passes.  

---

## 1. Core Idea
Core principles of {title}.

## 2. Core Heuristic & Trigger
- **When in {domain} decisions** → Prioritize **Reversible experiments** over _Irreversible lock-in_ because risk control. (Rule: `Classify reversibility before commit`) [Tier {tier}] [Tags: {domain}]
- **The Core Question / Razor:** "Can this decision be reversed cheaply?"
- **Governing Invariant:** Reversibility bounds long-term regret

## 3. Mental Moves / Procedures
1. Audit reversibility classification.

## 4. Where to Apply
- **Primary Domain:** {domain}

### Ontology Primitives
- **Reversibility** (`variable`): Ease and cost of undoing a choice.

### Trade-Off Matrix
| Tension Dimension | Recommended Choice | Sacrificed | Gained | Boundary Flip Condition |
| :--- | :--- | :--- | :--- | :--- |
| Speed vs Certainty | Fast reversal | Absolute proof | Fast cycle time | Permanent data corruption |

## 5. Anti-Patterns & Boundaries (When it Breaks)
- **Tattoo in Disguise**: Treating an irreversible decision as easily reversible → Catastrophic lock-in (Recovery: Require explicit rollback plan)

## 6. Source Genealogy & Cousins
- **Lineage:** Decision Science
- **Cousins:** None
<!-- NOETIC:AUTO:END -->

<!-- NOETIC:LOG:START -->
## Applications Log
-
<!-- NOETIC:LOG:END -->
{extra_human_text}
"""
  fw_file.write_text(content, encoding="utf-8")
  if status == "approved":
    set_status(fw_file, "approved")
  elif status != "pending_review":
    set_status(fw_file, status)
  return fw_file


def _sample_adr_data(adr_number: str = "ADR-001", title: str = "Adopt SQLite Local Engine") -> dict:
  return {
    "schema_version": "1.0.0",
    "adr_number": adr_number,
    "title": title,
    "status": "pending_review",
    "target_doc": "RFC-042: Storage Engine",
    "evaluated_frameworks": ["hats-haircuts-and-tattoos", "boring-technology"],
    "context_and_problem": "Need deterministic sub-16ms query latency and offline durability without distributed locks.",
    "reversibility": {
      "classification": "haircut",
      "rationale": "Storage engine is modular; repository interface permits swap to IndexedDB if needed.",
      "rollback_plan": "Maintain schema export pipeline and fallback json file storage for 30 days."
    },
    "complexity_audit": {
      "tokens_spent": 1,
      "token_budget": 3,
      "rationale": "SQLite is rock-solid and well-understood; costs 1 token for WASM runtime integration.",
      "simpler_alternatives": [
        "In-memory JS dictionary with localstorage flush (lacks transactions and indexed queries)"
      ]
    },
    "framework_compliance": [
      {
        "framework": "boring-technology",
        "check_name": "Spend innovation tokens deliberately",
        "verdict": "pass",
        "critique": "SQLite is one of the most thoroughly tested and boring technologies on Earth.",
        "risk": "WASM memory footprint on resource-constrained devices."
      },
      {
        "framework": "hats-haircuts-and-tattoos",
        "check_name": "Classify every decision before executing",
        "verdict": "pass",
        "critique": "Correctly classified as haircut with documented rollback.",
        "risk": "Unsynced local mutations during forced rollback."
      }
    ],
    "unresolved_tensions": [
      {
        "tension_dimension": "Binary Size vs Query Power",
        "conflicting_frameworks": ["boring-technology", "minimal-bundle"],
        "conflicting_heuristics": ["Prefer battle-tested database", "Keep client payload minimal"],
        "escalation_note": "Adds 800KB bundle overhead. Human owner should confirm mobile browser target."
      }
    ],
    "decision_outcome": {
      "outcome": "accepted",
      "justification": "Robustness and ACID guarantees outweigh the 800KB payload penalty.",
      "consequences": "High performance local search and zero data loss on crash."
    },
    "provenance": "Generated by Mode B sparring pipeline (spar) run test-run on 2026-11-09."
  }


@pytest.fixture
def mock_spar_agent(monkeypatch):
  """Intercepts agent_step to return schema-valid ADR critique without running LLMs."""
  def fake_run_agent(name, prompt, schema, **kw):
    return AgentResult(name, True, data=_sample_adr_data(), seconds=0.1)
  monkeypatch.setattr(steps_mod, "run_agent", fake_run_agent)


def test_spar_default_lenses_from_config(vault, mock_spar_agent):
  """Verify spar reads default_lenses from noetic.config.json with zero hardcoding [R2]."""
  # Create approved default lenses
  _make_lens(vault, "hats-haircuts-and-tattoos", "Hats, Haircuts, and Tattoos", tier=4, domain="governance")
  _make_lens(vault, "boring-technology", "Choose Boring Technology", tier=2, domain="architecture")

  rfc = vault / "RFC-001.md"
  rfc.write_text("# RFC 001: Local Cache\nUse SQLite WASM for local persistence.", encoding="utf-8")

  cfg = Config(vault, json.loads((vault / CONFIG_NAME).read_text(encoding="utf-8")))
  run = Run(cfg, "spar", {"target": str(rfc)})
  out = spar(run, {"target": str(rfc)})

  assert len(out) == 1
  adr_path = vault / out[0]
  assert adr_path.exists()
  text = adr_path.read_text(encoding="utf-8")
  assert "ADR-001" in text
  assert "hats-haircuts-and-tattoos" in text
  assert "boring-technology" in text


def test_spar_custom_default_lenses_from_config(vault, mock_spar_agent):
  """Verify spar dynamically respects custom default_lenses defined in config [R2]."""
  custom_cfg = {
    "owner": "Tester",
    "agents": ["claude", "agy", "codex"],
    "default_lenses": ["custom-lens-one"],
    "paths": {"frameworks": "frameworks"}
  }
  (vault / CONFIG_NAME).write_text(json.dumps(custom_cfg), encoding="utf-8")
  _make_lens(vault, "custom-lens-one", "Custom Lens One", tier=1, domain="taste")

  rfc = vault / "RFC-002.md"
  rfc.write_text("# RFC 002: Simple Design", encoding="utf-8")

  cfg = Config(vault, custom_cfg)
  run = Run(cfg, "spar", {"target": str(rfc)})
  out = spar(run, {"target": str(rfc)})

  adr_path = vault / out[0]
  assert adr_path.exists()
  text = adr_path.read_text(encoding="utf-8")
  assert "custom-lens-one" in text


def test_spar_user_frameworks_appended_and_deduplicated(vault, mock_spar_agent):
  """Verify user-provided frameworks are appended to default lenses and deduplicated [R2]."""
  _make_lens(vault, "hats-haircuts-and-tattoos", "Hats Haircuts Tattoos", tier=4)
  _make_lens(vault, "boring-technology", "Boring Tech", tier=2)
  _make_lens(vault, "c4-model", "C4 Architectural Model", tier=2)

  rfc = vault / "RFC-003.md"
  rfc.write_text("# RFC 003: Architecture", encoding="utf-8")

  cfg = Config(vault, json.loads((vault / CONFIG_NAME).read_text(encoding="utf-8")))
  run = Run(cfg, "spar", {"target": str(rfc), "frameworks": ["boring-technology", "c4-model"]})
  out = spar(run, {"target": str(rfc), "frameworks": ["boring-technology", "c4-model"]})

  adr_path = vault / out[0]
  text = adr_path.read_text(encoding="utf-8")
  assert "c4-model" in text
  # Ensure boring-technology is not duplicated in frontmatter
  assert text.count('"boring-technology"') == 1


def test_spar_fails_loudly_when_lens_missing(vault):
  """Verify spar fails loudly when a default or requested lens is missing [R1+R2]."""
  _make_lens(vault, "hats-haircuts-and-tattoos", "Hats Haircuts Tattoos")
  # boring-technology is missing!

  rfc = vault / "RFC-004.md"
  rfc.write_text("# RFC 004", encoding="utf-8")

  cfg = Config(vault, json.loads((vault / CONFIG_NAME).read_text(encoding="utf-8")))
  run = Run(cfg, "spar", {"target": str(rfc)})

  with pytest.raises(PipelineError) as exc_info:
    spar(run, {"target": str(rfc)})

  err = exc_info.value.payload
  assert err["code"] == "LENS_UNAVAILABLE"
  assert "boring-technology" in err["detail"]


def test_spar_fails_loudly_when_lens_unapproved(vault):
  """Verify spar fails loudly when any lens is not approved [R1+R2]."""
  _make_lens(vault, "hats-haircuts-and-tattoos", "Hats Haircuts Tattoos", status="approved")
  _make_lens(vault, "boring-technology", "Boring Tech", status="pending_review")

  rfc = vault / "RFC-005.md"
  rfc.write_text("# RFC 005", encoding="utf-8")

  cfg = Config(vault, json.loads((vault / CONFIG_NAME).read_text(encoding="utf-8")))
  run = Run(cfg, "spar", {"target": str(rfc)})

  with pytest.raises(PipelineError) as exc_info:
    spar(run, {"target": str(rfc)})

  err = exc_info.value.payload
  assert err["code"] == "LENS_UNAVAILABLE"
  assert "not approved" in err["detail"] or "failed trust" in err["detail"]


def test_spar_fails_loudly_when_lens_tampered(vault):
  """Verify spar rejects a lens whose content hash was tampered post-approval [R1]."""
  fw = _make_lens(vault, "hats-haircuts-and-tattoos", "Hats Haircuts Tattoos", status="approved")
  _make_lens(vault, "boring-technology", "Boring Tech", status="approved")

  # Tamper with fw note content
  raw = fw.read_text(encoding="utf-8")
  fw.write_text(raw + "\nMalicious injection post approval", encoding="utf-8")

  rfc = vault / "RFC-006.md"
  rfc.write_text("# RFC 006", encoding="utf-8")

  cfg = Config(vault, json.loads((vault / CONFIG_NAME).read_text(encoding="utf-8")))
  run = Run(cfg, "spar", {"target": str(rfc)})

  with pytest.raises(PipelineError) as exc_info:
    spar(run, {"target": str(rfc)})

  err = exc_info.value.payload
  assert err["code"] == "LENS_UNAVAILABLE"
  assert "failed trust policy" in err["detail"] or "APPROVAL_HASH_MISMATCH" in err["detail"]


def test_spar_fails_loudly_when_target_missing(vault):
  """Verify spar raises TARGET_NOT_FOUND when target file is missing."""
  _make_lens(vault, "hats-haircuts-and-tattoos", "Hats", status="approved")
  _make_lens(vault, "boring-technology", "Boring", status="approved")

  cfg = Config(vault, json.loads((vault / CONFIG_NAME).read_text(encoding="utf-8")))
  run = Run(cfg, "spar", {"target": "nonexistent_rfc.md"})

  with pytest.raises(PipelineError) as exc_info:
    spar(run, {"target": "nonexistent_rfc.md"})

  assert exc_info.value.payload["code"] == "TARGET_NOT_FOUND"


def test_atomic_adr_numbering_sequential(tmp_path):
  """Verify atomic ADR numbering increments safely from ADR-001 [R1]."""
  adr_dir = tmp_path / "adr"
  adr_dir.mkdir()

  assert next_atomic_adr_number(adr_dir) == "ADR-001"

  (adr_dir / "ADR-001-init.md").write_text("# ADR 001", encoding="utf-8")
  assert next_atomic_adr_number(adr_dir) == "ADR-002"

  (adr_dir / "ADR-002-cache.md").write_text("# ADR 002", encoding="utf-8")
  assert next_atomic_adr_number(adr_dir) == "ADR-003"

  # Non-contiguous numbering jumps to highest + 1
  (adr_dir / "ADR-010-future.md").write_text("# ADR 010", encoding="utf-8")
  assert next_atomic_adr_number(adr_dir) == "ADR-011"


def test_atomic_adr_numbering_concurrency(tmp_path):
  """Verify concurrent requests for next ADR number under lock never produce duplicates [R1]."""
  adr_dir = tmp_path / "concurrent_adr"
  adr_dir.mkdir()

  assigned_numbers = []

  def assign_one(worker_id):
    num, path = reserve_next_adr_number(adr_dir, slug=f"worker-{worker_id}")
    assigned_numbers.append(num)
    return num

  with ThreadPoolExecutor(max_workers=8) as ex:
    futures = [ex.submit(assign_one, i) for i in range(12)]
    results = [f.result() for f in futures]

  # All 12 assigned numbers must be unique
  assert len(results) == 12
  assert len(set(results)) == 12
  expected = [f"ADR-{i:03d}" for i in range(1, 13)]
  assert sorted(results) == expected


def test_adr_note_creation_and_approval_lifecycle(vault, mock_spar_agent):
  """Verify ADR note creation with status: pending_review and lifecycle transition to accepted [R1]."""
  _make_lens(vault, "hats-haircuts-and-tattoos", "Hats", status="approved")
  _make_lens(vault, "boring-technology", "Boring", status="approved")

  rfc = vault / "RFC-010.md"
  rfc.write_text("# RFC 010: State Sync", encoding="utf-8")

  cfg = Config(vault, json.loads((vault / CONFIG_NAME).read_text(encoding="utf-8")))
  run = Run(cfg, "spar", {"target": str(rfc)})
  out = spar(run, {"target": str(rfc)})

  adr_path = vault / out[0]
  assert adr_path.exists()
  text = adr_path.read_text(encoding="utf-8")

  # Invariant checks on generated note
  assert "status: pending_review" in text
  assert "type: adr" in text
  assert "schema_version: 1.0.0" in text
  assert AUTO_START in text and AUTO_END in text
  assert "## 1. Context and Problem Statement" in text
  assert "## 2. Reversibility Assessment (Decision Classification)" in text
  assert "## 3. Complexity & Innovation Tokens Audit" in text
  assert "## 4. Framework Compliance & Sparring Audit" in text
  assert "## 5. Unresolved Tensions & Escalations" in text
  assert "## 6. Decision Outcome" in text

  # Test gate approval transition to accepted [R1]
  gate.approve(adr_path)
  approved_text = adr_path.read_text(encoding="utf-8")
  assert "status: accepted" in approved_text
  assert 'approval_hash: "' in approved_text
  assert gate.status_of(adr_path) == "accepted"
  gate.require_approved(adr_path, verify_hash=True)


def test_spar_preserves_human_edits_outside_markers(vault, mock_spar_agent):
  """Verify human edits outside <!-- NOETIC:AUTO:START/END --> survive subsequent updates [R1+R2]."""
  _make_lens(vault, "hats-haircuts-and-tattoos", "Hats", status="approved")
  _make_lens(vault, "boring-technology", "Boring", status="approved")

  rfc = vault / "RFC-020.md"
  rfc.write_text("# RFC 020: Messaging Protocol", encoding="utf-8")

  cfg = Config(vault, json.loads((vault / CONFIG_NAME).read_text(encoding="utf-8")))
  run1 = Run(cfg, "spar", {"target": str(rfc)})
  out = spar(run1, {"target": str(rfc)})

  adr_path = vault / out[0]
  initial_text = adr_path.read_text(encoding="utf-8")

  # Human adds review comments outside the AUTO block
  human_comment = "\n\n### Human Architect Override Note\nWe decided to accept despite the WASM memory concern because desktop is our primary target."
  adr_path.write_text(initial_text + human_comment, encoding="utf-8")

  # Run spar again updating the same ADR
  run2 = Run(cfg, "spar", {"target": str(rfc), "adr_number": "ADR-001"})
  spar(run2, {"target": str(rfc), "adr_number": "ADR-001"})

  updated_text = adr_path.read_text(encoding="utf-8")
  assert human_comment in updated_text
  assert AUTO_START in updated_text and AUTO_END in updated_text


def test_spar_updates_framework_applications_log_inside_markers(vault, mock_spar_agent):
  """Verify Applications Log is appended strictly inside LOG markers without touching human text [R2]."""
  human_note = "\n## My Personal Field Experience\nThis framework saved us during the 2024 database migration."
  fw1 = _make_lens(vault, "hats-haircuts-and-tattoos", "Hats", status="approved", extra_human_text=human_note)
  fw2 = _make_lens(vault, "boring-technology", "Boring", status="approved", extra_human_text=human_note)

  rfc = vault / "RFC-030.md"
  rfc.write_text("# RFC 030: Database Migration", encoding="utf-8")

  cfg = Config(vault, json.loads((vault / CONFIG_NAME).read_text(encoding="utf-8")))
  run = Run(cfg, "spar", {"target": str(rfc)})
  spar(run, {"target": str(rfc)})

  # Check fw1 log and preservation of human note
  fw1_text = fw1.read_text(encoding="utf-8")
  assert LOG_START in fw1_text and LOG_END in fw1_text
  log_block = fw1_text.split(LOG_START)[1].split(LOG_END)[0]
  assert f"- {today()} · project · [[ADR-001-adopt-sqlite-local-engine]]" in log_block
  assert human_note in fw1_text  # Human text preserved verbatim!

  # Check fw2 log and preservation of human note
  fw2_text = fw2.read_text(encoding="utf-8")
  log_block_2 = fw2_text.split(LOG_START)[1].split(LOG_END)[0]
  assert f"- {today()} · project · [[ADR-001-adopt-sqlite-local-engine]]" in log_block_2
  assert human_note in fw2_text


def test_spar_inline_text_target(vault, mock_spar_agent):
  """Verify spar accepts inline text/diff proposals directly."""
  _make_lens(vault, "hats-haircuts-and-tattoos", "Hats", status="approved")
  _make_lens(vault, "boring-technology", "Boring", status="approved")

  inline_diff = """
  diff --git a/storage/db.py b/storage/db.py
  +import sqlite3
  +def get_conn():
  +  return sqlite3.connect(":memory:")
  """

  cfg = Config(vault, json.loads((vault / CONFIG_NAME).read_text(encoding="utf-8")))
  run = Run(cfg, "spar", {"target": inline_diff})
  out = spar(run, {"target": inline_diff})

  adr_path = vault / out[0]
  assert adr_path.exists()
  text = adr_path.read_text(encoding="utf-8")
  assert "ADR-001" in text
