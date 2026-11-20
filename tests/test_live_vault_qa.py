"""Phase 5 Live Vault End-to-End QA Test [R1+R2].

Simulates an end-to-end cognitive compilation cycle in a realistic temporary vault:
1. Ingest pipeline on a real engineering text (Raft consensus and state machine replication).
2. Note layout verification: lands in frameworks/ with status: pending_review,
   canonical 5-point layout, schema_version: 1.0.0, and machine markers.
3. Human approval lifecycle: gate.approve transitions note to status: approved
   and records cryptographic approval_hash.
4. Mode B Sparring against a sample RFC: generates an ADR note with status: pending_review,
   atomic numbering (ADR-001), and updates the framework's Applications Log strictly
   inside machine markers without invalidating the approval hash.
5. Non-clobbering preservation: human notes outside machine markers survive re-ingest
   and trigger needs_merge_review with proposed enrichment.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from noetic.agents.runners import AgentResult
from noetic.gates import gate
from noetic.knowledge import notes
from noetic.knowledge.config import CONFIG_NAME, Config
from noetic.knowledge.notes import (
    AUTO_END,
    AUTO_START,
    LOG_END,
    LOG_START,
    PROPOSED_END,
    PROPOSED_START,
    TABLE_END,
    TABLE_START,
    get_approval_hash,
    status_of,
    verify_approval_hash,
)
from noetic.knowledge.stack import check_framework_trust
from noetic.mcp.server import create_mcp_server
from noetic.orchestration import steps as steps_mod
from noetic.orchestration.run import Run
from workflows.taste_engine.pipelines.ingest import ingest
from workflows.taste_engine.pipelines.spar import spar


# ── Sample Engineering Ground Truth & Agent Mocks ────────────────────────────


def sample_raft_engineering_text() -> str:
  return """# In Search of an Understandable Consensus Algorithm (Ongaro & Ousterhout 2014)

Raft is a consensus algorithm for managing a replicated state machine.
It decomposes consensus into three independent subproblems:
1. Leader Election: A new leader must be chosen when an existing leader fails.
   Servers begin as followers. If they receive no communication, they time out,
   become candidates, and request votes. A candidate receiving votes from a majority
   of servers becomes leader for that term.
2. Log Replication: The leader accepts log entries from clients, replicates them
   across other servers, and tells servers when it is safe to apply log entries to
   their state machines. A log entry is committed once it is replicated on a majority of nodes.
3. Safety: If a server has applied a particular log entry to its state machine, no other
   server may apply a different log entry for the same log index. Leaders never overwrite
   or truncate their own log entries.

Anti-Pattern: Split-Brain Commit Trap. Allowing minority partitions to accept client writes
leads to irrecoverable divergent state. Raft guarantees safety by requiring majority quorums
for both leader election and entry commitment.
"""


def sample_raft_extraction() -> dict:
  return {
      "schema_version": "1.0.0",
      "title": "In Search of an Understandable Consensus Algorithm (Raft)",
      "source_metadata": {
          "title": "In Search of an Understandable Consensus Algorithm",
          "author": "Diego Ongaro and John Ousterhout",
          "kind": "paper",
          "url": "https://raft.github.io/raft.pdf",
      },
      "entities": [
          "Leader",
          "Follower",
          "Candidate",
          "Term",
          "Log Entry",
          "Majority Quorum",
          "State Machine",
      ],
      "core_principles": [
          {
              "name": "Decomposed State Machine Consensus",
              "description": "Decomposing consensus into leader election, log replication, and safety makes it understandable and verifiable.",
          },
          {
              "name": "Quorum-Backed Commit Safety",
              "description": "Log entries are only committed and applied to state machines once acknowledged by a strict majority of nodes.",
          },
          {
              "name": "Monotonic Leader Terms",
              "description": "Time is divided into terms with monotonic integer IDs; candidates step down immediately if a higher term is observed.",
          },
      ],
      "mental_moves": [
          "Decompose multi-node consensus into election, replication, and safety.",
          "Require strict majority quorum (N/2 + 1) for both leader election and log entry commits.",
          "Step down immediately to follower upon encountering a higher term number in RPC responses.",
          "Reject append entries if the previous log index and term do not match leader state.",
      ],
      "anti_patterns": [
          {
              "trap_name": "Split-Brain Commit Trap",
              "symptom": "Divergent state histories across disconnected network partitions",
              "failure_mechanism": "Permitting writes to commit on minority partitions without quorum consensus",
              "recovery_move": "Fence minority partitions and require majority quorum before acknowledging writes.",
          }
      ],
      "genealogy": ["Paxos", "Viewstamped Replication", "Chubby"],
      "rejected": False,
      "rejection_reason": "",
      "is_signal": True,
      "signal_data": {"clarity": 5.0, "rigor": 5.0},
      "harness_notes": [],
  }


def sample_raft_cognitive_framework() -> dict:
  return {
      "schema_version": "1.0.0",
      "framework_name": "Raft Consensus and State Machine Replication",
      "slug": "raft-consensus",
      "source": {
          "title": "In Search of an Understandable Consensus Algorithm",
          "author": "Diego Ongaro and John Ousterhout",
          "kind": "paper",
          "url": "https://raft.github.io/raft.pdf",
      },
      "evaluation_rubric": {
          "the_keyboard_test": "Replicated state machine deterministically recovers from single-node crash in <500ms with zero manual intervention.",
          "admission_test_scores": {
              "executable_heuristic": 5,
              "cognitive_compression": 5,
              "keyboard_test": 5,
              "explicit_failure_mode": 5,
              "cross_domain_transfer": 4,
          },
          "falsification_criteria": "If a split network partition allows two distinct leaders to commit differing log entries for the same index, Raft consensus is falsified.",
      },
      "ontology": {
          "domain": "Distributed Systems",
          "primitives": [
              {
                  "name": "Term",
                  "kind": "variable",
                  "definition": "Monotonically increasing logical clock serving as leader lease boundary.",
                  "observable_indicator": "Integer term counter attached to every RPC.",
              },
              {
                  "name": "Majority Quorum",
                  "kind": "force",
                  "definition": "Strict majority (N/2 + 1) of cluster servers required to authorize any commit.",
                  "observable_indicator": "Vote count threshold across active nodes.",
              },
          ],
          "governing_invariant": "Committed entries are durable and guaranteed to be present in all future leaders.",
      },
      "directional_heuristics": [
          {
              "context": "When designing replicated distributed storage",
              "prioritize": "Quorum-backed leader consensus",
              "over": "Multi-master uncoordinated writes",
              "because": "Decomposing consensus into single-leader terms eliminates split-brain data divergence",
              "operational_rule": "Require majority quorum acknowledgement before acknowledging client mutations",
              "tier": 2,
              "domain_tags": ["distributed-systems", "consensus", "storage"],
              "provenance_anchor": "Ongaro 2014 Section 5.2",
          }
      ],
      "trade_off_matrix": [
          {
              "dimension": "Write Availability vs State Consistency",
              "recommended_choice": "Quorum synchronization wait",
              "sacrificed": "Immediate sub-millisecond local return on disconnected partitions",
              "gained": "Linearizable consistency and zero data corruption across partitions",
              "boundary_flip_condition": "When building single-device local caches where offline operation is mandatory",
          }
      ],
      "anti_patterns": [
          {
              "trap_name": "Split-Brain Commit Trap",
              "symptom": "Divergent state histories across disconnected network partitions",
              "failure_mechanism": "Permitting writes to commit on minority partitions without quorum consensus",
              "recovery_move": "Fence minority partitions and require majority quorum before acknowledging writes.",
          }
      ],
      "faithful_layer": {
          "core_idea": "Consensus is made practical by decomposing it into leader election, log replication, and safety.",
          "razor": "Can a minority partition commit writes? If yes, the architecture violates consensus safety.",
          "mental_moves": [
              "Elect leader via majority quorum.",
              "Replicate log sequentially through single leader.",
              "Step down immediately upon seeing a higher term.",
          ],
      },
      "applied_layer": {
          "linked_interests": ["Distributed Systems", "Architecture"],
          "stance_alignments": ["Deterministic Replicated State Machines"],
          "stance_conflicts": ["Uncoordinated Multi-Master Writes"],
      },
      "genealogy": ["Paxos", "Viewstamped Replication"],
      "harness_notes": [],
  }


def sample_rfc_proposal() -> str:
  return """# RFC-042: High-Throughput Replicated Event Bus

## Abstract
Proposes an in-memory event bus with multi-leader replication where any node
accepts client writes immediately without waiting for cluster quorum synchronization.

## Proposed Architecture
- Multi-master: Every replica accepts write mutations locally and asynchronously floods updates.
- No leader election: Nodes do not elect leaders or track terms.
- Low latency: Returns HTTP 200 OK before remote nodes acknowledge.

## Questions for Architecture Sparring
- Does this violate core consistency invariants?
- What are the failure modes during a WAN partition?
"""


def sample_adr_critique_data() -> dict:
  return {
      "schema_version": "1.0.0",
      "adr_number": "ADR-001",
      "title": "Critique of RFC-042 Multi-Master Event Bus",
      "status": "pending_review",
      "target_doc": "RFC-042: High-Throughput Replicated Event Bus",
      "evaluated_frameworks": ["raft-consensus"],
      "context_and_problem": "RFC-042 proposes multi-master uncoordinated writes without quorums to achieve low latency, but risks data corruption during network partitions.",
      "reversibility": {
          "classification": "haircut",
          "rationale": "Event bus protocol is behind an internal client library interface; can be migrated back to single-leader coordinator with 2 weeks of effort.",
          "rollback_plan": "Maintain dual-write adapter and fallback to centralized PostgreSQL event table if divergence occurs.",
      },
      "complexity_audit": {
          "tokens_spent": 1,
          "token_budget": 3,
          "rationale": "Novel multi-master event replication costs 1 innovation token; high risk of subtle distributed edge cases.",
          "simpler_alternatives": [
              "Boring single-leader Raft consensus queue (Kafka or NATS JetStream)",
              "Single PostgreSQL instance with CDC log tailing",
          ],
      },
      "framework_compliance": [
          {
              "framework": "raft-consensus",
              "check_name": "Quorum-backed leader consensus",
              "verdict": "fail",
              "critique": "RFC-042 accepts writes without majority quorum, directly violating the governing invariant of Raft consensus.",
              "risk": "Irrecoverable split-brain data divergence when network partitions occur.",
          }
      ],
      "unresolved_tensions": [
          {
              "tension_dimension": "Write Latency vs Consistency Safety",
              "conflicting_frameworks": ["raft-consensus", "optimistic-local-writes"],
              "conflicting_heuristics": ["Require quorum acknowledgment", "Return sub-millisecond local write"],
              "escalation_note": "Uncoordinated writes produce silent data loss under partitions. Human sign-off required to confirm if data loss is tolerable.",
          }
      ],
      "decision_outcome": {
          "outcome": "rejected",
          "justification": "Violates distributed consensus invariants; uncoordinated writes cause split-brain data divergence.",
          "consequences": "Adopt single-leader Raft consensus queue instead of custom multi-master replication.",
      },
      "provenance": "Generated by Mode B sparring pipeline (spar) run test-live-vault on 2026-11-09.",
  }


# ── Live Vault End-to-End QA Test ───────────────────────────────────────────


def test_live_vault_end_to_end_qa(tmp_path: Path, monkeypatch):
  """Simulate a complete end-to-end cognitive compilation cycle in a temporary vault.

  Steps:
  1. Ingest engineering text -> verify note layout, markers, pending_review status.
  2. Human approval -> verify approval_hash computation and trust policy.
  3. Mode B Sparring -> verify ADR generation, atomic numbering, Applications Log appending.
  4. Non-clobbering edits -> verify human notes preserved and merge review triggered.
  """
  # 1. Initialize realistic vault on disk
  vault = tmp_path / "live_qa_vault"
  vault.mkdir()
  (vault / "frameworks").mkdir()
  (vault / "sources").mkdir()
  (vault / "Reading").mkdir()
  (vault / "wiki" / "adr").mkdir(parents=True)
  (vault / ".noetic").mkdir()

  config_data = {
      "owner": "Engineering Lead",
      "agents": ["claude", "agy", "codex"],
      "schema_version": "1.0.0",
      "default_lenses": ["raft-consensus"],
      "similarity_thresholds": {
          "tier1_slug_exact": 1.0,
          "tier2_cousin_semantic": 0.85,
      },
      "mcp_serve_policy": {
          "require_approved": True,
          "verify_hash": True,
      },
      "budget": {
          "per_run_usd": 10.00,
      },
  }
  (vault / CONFIG_NAME).write_text(json.dumps(config_data, indent=2), encoding="utf-8")
  cfg = Config(vault, config_data)

  # Write source engineering paper to Reading/
  source_file = vault / "Reading" / "raft-paper.md"
  source_file.write_text(sample_raft_engineering_text(), encoding="utf-8")

  # 2. Mock Agent Steps for Ingest
  def fake_run_agent_ingest(agent, prompt, schema, **kw):
    title = schema.get("title", "")
    if title == "extraction":
      return AgentResult(agent, True, data=sample_raft_extraction(), seconds=0.2, cost_usd=0.02)
    if title == "cognitive_framework":
      return AgentResult(agent, True, data=sample_raft_cognitive_framework(), seconds=0.3, cost_usd=0.05)
    return AgentResult(agent, True, data={}, seconds=0.1)

  monkeypatch.setattr(steps_mod, "run_agent", fake_run_agent_ingest)

  # Run ingest pipeline
  ingest_run = Run(cfg, "ingest", {"source": "Reading/raft-paper.md"})
  ingest_outputs = ingest(ingest_run, {"source": "Reading/raft-paper.md"})

  assert len(ingest_outputs) == 2, "Ingest must output [framework_note, source_note]"
  fw_rel, src_rel = ingest_outputs[0], ingest_outputs[1]

  fw_path = cfg.vault / fw_rel
  src_path = cfg.vault / src_rel
  assert fw_path.exists(), f"Framework note was not created at {fw_path}"
  assert src_path.exists(), f"Source note was not created at {src_path}"

  fw_text = fw_path.read_text(encoding="utf-8")

  # 3. Verify Note Layout, Frontmatter & Markers
  assert "status: pending_review" in fw_text
  assert "schema_version: 1.0.0" in fw_text
  assert 'approval_hash: ""' in fw_text
  assert status_of(fw_path) == "pending_review"

  # Machine markers
  assert AUTO_START in fw_text and AUTO_END in fw_text
  assert LOG_START in fw_text and LOG_END in fw_text
  assert PROPOSED_START in fw_text and PROPOSED_END in fw_text

  # Canonical 5-Point Layout
  assert "# Framework: Raft Consensus and State Machine Replication" in fw_text
  assert "**Admission Score:**" in fw_text
  assert "**The Keyboard Test:**" in fw_text
  assert "## 1. Core Idea" in fw_text
  assert "## 2. Core Heuristic & Trigger" in fw_text
  assert "[Tier 2]" in fw_text
  assert "[Tags: distributed-systems, consensus, storage]" in fw_text
  assert "[Anchor: Ongaro 2014 Section 5.2]" in fw_text
  assert "## 3. Mental Moves / Procedures" in fw_text
  assert "## 4. Where to Apply" in fw_text
  assert "### Ontology Primitives" in fw_text
  assert "### Trade-Off Matrix" in fw_text
  assert "## 5. Anti-Patterns & Boundaries (When it Breaks)" in fw_text
  assert "## 6. Source Genealogy & Cousins" in fw_text
  assert "Paxos" in fw_text

  # Master Catalog Table updated
  readme_path = cfg.frameworks / "README.md"
  assert readme_path.exists()
  readme_text = readme_path.read_text(encoding="utf-8")
  assert TABLE_START in readme_text and TABLE_END in readme_text
  assert "raft-consensus" in readme_text
  assert "pending_review" in readme_text

  # 4. Human Approval Flow
  # Before approval, MCP trust policy refuses the unapproved note
  ok_before, err_before = check_framework_trust(fw_path, include_unapproved=False, verify_hash=True)
  assert ok_before is False
  assert "not approved" in err_before

  # Human review and approval
  approval_note = "Approved by Tech Lead: fully verified against Raft specification."
  gate.approve(fw_path, approval_note)

  # Verification after approval
  assert status_of(fw_path) == "approved"
  app_hash = get_approval_hash(fw_path)
  assert app_hash is not None and len(app_hash) == 64
  assert verify_approval_hash(fw_path) is True

  ok_after, err_after = check_framework_trust(fw_path, include_unapproved=False, verify_hash=True)
  assert ok_after is True
  assert err_after == ""

  # MCP server serves approved note
  server = create_mcp_server(vault_override=vault)
  tools = {t.name: t for t in server._tool_manager.list_tools()}
  get_fw_res = tools["get_framework"].fn(slug="raft-consensus")
  assert get_fw_res["ok"] is True
  assert get_fw_res["slug"] == "raft-consensus"

  # 5. Mode B Sparring against Sample RFC
  rfc_file = vault / "RFC-042.md"
  rfc_file.write_text(sample_rfc_proposal(), encoding="utf-8")

  def fake_run_agent_spar(agent, prompt, schema, **kw):
    title = schema.get("title", "")
    if title == "adr":
      return AgentResult(agent, True, data=sample_adr_critique_data(), seconds=0.4, cost_usd=0.08)
    return AgentResult(agent, True, data={}, seconds=0.1)

  monkeypatch.setattr(steps_mod, "run_agent", fake_run_agent_spar)

  spar_run = Run(cfg, "spar", {"target": str(rfc_file), "frameworks": ["raft-consensus"]})
  spar_outputs = spar(spar_run, {"target": str(rfc_file), "frameworks": ["raft-consensus"]})

  assert len(spar_outputs) == 1
  adr_rel = spar_outputs[0]
  adr_path = cfg.vault / adr_rel
  assert adr_path.exists()

  adr_text = adr_path.read_text(encoding="utf-8")

  # Verify ADR Note properties
  assert "status: pending_review" in adr_text
  assert "schema_version: 1.0.0" in adr_text
  assert "ADR-001" in adr_text
  assert AUTO_START in adr_text and AUTO_END in adr_text
  assert "Critique of RFC-042" in adr_text
  assert "Quorum-backed leader consensus" in adr_text

  # Verify Applications Log in framework note was updated
  fw_text_after_spar = fw_path.read_text(encoding="utf-8")
  assert LOG_START in fw_text_after_spar and LOG_END in fw_text_after_spar
  assert adr_path.stem in fw_text_after_spar

  # Invariant: Approval hash remains VALID because log block is normalized away [R1+R2]
  assert verify_approval_hash(fw_path) is True

  # 6. Non-Clobbering Human Edits and Merge Protection
  human_custom_text = "\n\n## Operations Lead Deployment Manual\n- Production quorum requires 5 nodes across 3 availability zones.\n"
  fw_path.write_text(fw_path.read_text(encoding="utf-8") + human_custom_text, encoding="utf-8")

  # Subsequent ingest run with same framework slug triggers MERGE
  monkeypatch.setattr(steps_mod, "run_agent", fake_run_agent_ingest)
  ingest_run_2 = Run(cfg, "ingest", {"source": "Reading/raft-paper.md"})
  ingest_outputs_2 = ingest(ingest_run_2, {"source": "Reading/raft-paper.md"})

  fw_text_after_merge = fw_path.read_text(encoding="utf-8")

  # Invariants:
  # - Target note was NOT overwritten in place
  # - Status transitioned to needs_merge_review
  # - Proposed enrichment appended inside PROPOSED markers
  # - Human custom deployment manual survived completely intact
  assert "status: needs_merge_review" in fw_text_after_merge
  assert PROPOSED_START in fw_text_after_merge and PROPOSED_END in fw_text_after_merge
  assert "### Proposed Enrichment" in fw_text_after_merge
  assert "## Operations Lead Deployment Manual" in fw_text_after_merge
  assert "Production quorum requires 5 nodes across 3 availability zones." in fw_text_after_merge
