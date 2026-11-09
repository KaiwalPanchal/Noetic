"""Tests for Mode A Multi-Framework Cognitive Stacking in replicate pipeline [Phase 3, R1, R2]."""

import json
from pathlib import Path
import subprocess

import pytest

from noetic.agents.runners import AgentResult
from noetic.gates.git import git
from noetic.knowledge.notes import set_status
from noetic.orchestration.run import PipelineError, Run
import noetic.orchestration.steps as steps_mod
from workflows.taste_engine.pipelines.replicate import replicate


def _make_cognitive_framework(
    vault: Path,
    slug: str,
    title: str,
    tier: int = 2,
    domain_tags: list[str] = None,
    prioritize: str = "Immediate local writes",
    over: str = "Remote blocking RPC",
    rule: str = "Commit locally first",
    status: str = "approved",
) -> Path:
  dtags = domain_tags or ["persistence"]
  tags_str = ", ".join(dtags)
  fw_file = vault / "frameworks" / f"{slug}.md"
  fw_file.parent.mkdir(parents=True, exist_ok=True)

  content = f"""---
author: ai-agent
status: pending_review
schema_version: 1.0.0
---
<!-- NOETIC:AUTO:START -->
# Framework: {title}

**Source:** {title} Author  
**Tags:** #framework #{dtags[0]}  
**Admission Score:** 4.7/5.0  
**The Keyboard Test:** No network latency.  

---

## 1. Core Idea
Core idea for {title}.

## 2. Core Heuristic & Trigger
- **When in {dtags[0]} decisions** → Prioritize **{prioritize}** over _{over}_ because durability. (Rule: `{rule}`) [Tier {tier}] [Tags: {tags_str}]
- **The Core Question / Razor:** "Can it run deterministically?"
- **Governing Invariant:** Consistency over convenience

## 3. Mental Moves / Procedures
1. Audit local state.

## 4. Where to Apply
- **Primary Domain:** {dtags[0]}

### Ontology Primitives
- **Local DB** (`state`): Authoritative replica on client device.

### Trade-Off Matrix
| Tension Dimension | Recommended Choice | Sacrificed | Gained | Boundary Flip Condition |
| :--- | :--- | :--- | :--- | :--- |
| Speed vs Coordination | Local writes | Global immediate order | Sub-16ms latency | Financial double spend |

## 5. Anti-Patterns & Boundaries (When it Breaks)
- **The Spinner Trap**: Blocking UI on remote HTTP calls → Latency spike (Recovery: Optimistic local mutation)

## 6. Source Genealogy & Cousins
- **Lineage:** Git
- **Cousins:** None
<!-- NOETIC:AUTO:END -->

<!-- NOETIC:LOG:START -->
## Applications Log
-
<!-- NOETIC:LOG:END -->
"""
  fw_file.write_text(content, encoding="utf-8")
  if status == "approved":
    set_status(fw_file, "approved")
  elif status != "pending_review":
    set_status(fw_file, status)
  return fw_file


def sample_ui_spec() -> dict:
  return {
      "title": "Minimal Fast Dashboard",
      "slug": "minimal-fast-dashboard",
      "goal": "Build a responsive dashboard inspired by linear speed",
      "references": [
          {"name": "Linear", "url": "https://linear.app", "stealing": "Instant command palette and keyboard latency"}
      ],
      "elements": [
          {
              "id": "E1",
              "name": "Navigation Bar",
              "seen_at": "https://linear.app",
              "what": "Minimalist header with command bar trigger",
              "implementation": "CSS flexbox + cmdk",
              "why_it_works": "Zero visual latency",
              "steal": "Command bar shortcut trigger",
              "transform": "Custom dark zinc theme",
          }
      ],
      "stack": "Next.js, Tailwind CSS, TypeScript",
      "do_not_copy": ["Linear proprietary brand marks"],
      "acceptance": ["Supports reduced motion", "Works at 375px mobile width"],
      "credits": ["Linear for command bar inspiration"],
      "harness_notes": [],
  }


def sample_build_report() -> dict:
  return {
      "summary": "Implemented minimal command bar navigation",
      "files_changed": ["components/Nav.tsx"],
      "elements_done": ["E1"],
      "elements_skipped": [],
      "how_to_preview": "pnpm dev and open localhost:3000",
      "harness_notes": [],
  }


@pytest.fixture
def mock_agent_step(monkeypatch):
  calls = []

  def fake_run_agent(agent, prompt, schema, **kw):
    calls.append({"agent": agent, "prompt": prompt, "schema": schema, "kw": kw})
    title = schema.get("title", "")
    if title == "ui_spec":
      return AgentResult(agent, True, data=sample_ui_spec(), seconds=0.1)
    if title == "build_report":
      return AgentResult(agent, True, data=sample_build_report(), seconds=0.1)
    return AgentResult(agent, True, data={}, seconds=0.1)

  monkeypatch.setattr(steps_mod, "run_agent", fake_run_agent)
  return calls


def test_replicate_multi_framework_brief_generation(cfg, mock_agent_step):
  """Verify replicate accepts multiple frameworks, synthesizes stacked charter, and appends to applications log."""
  _make_cognitive_framework(cfg.vault, "linear-speed", "Linear Speed", tier=3, domain_tags=["ui-motion"],
                            prioritize="Instant visual state updates", over="Waiting for remote ack",
                            rule="Update DOM within 16ms")
  _make_cognitive_framework(cfg.vault, "local-sync", "Local Sync", tier=2, domain_tags=["persistence"],
                            prioritize="Local SQLite commit", over="Remote RPC blocking calls",
                            rule="Write to local database synchronously")

  run = Run(cfg, "replicate", {"frameworks": ["linear-speed", "local-sync"], "urls": ["https://linear.app"]})
  outputs = replicate(run, {"frameworks": ["linear-speed", "local-sync"], "urls": ["https://linear.app"]})

  assert len(outputs) == 1
  brief_rel = outputs[0]
  brief_path = cfg.vault / brief_rel
  assert brief_path.exists()

  brief_text = brief_path.read_text(encoding="utf-8")
  # Multi-framework frontmatter
  assert 'framework: "[[linear-speed]], [[local-sync]]"' in brief_text
  assert "# Build Brief: Minimal Fast Dashboard" in brief_text
  assert "## Element Breakdown" in brief_text

  # Injected heuristics check: deconstruct agent saw both frameworks and harmonized heuristics
  deconstruct_call = mock_agent_step[0]
  assert "linear-speed" in deconstruct_call["prompt"]
  assert "local-sync" in deconstruct_call["prompt"]
  assert "Instant visual state updates" in deconstruct_call["prompt"]
  assert "Local SQLite commit" in deconstruct_call["prompt"]

  # Applications log updated on both framework files
  fw1_text = (cfg.vault / "frameworks" / "linear-speed.md").read_text(encoding="utf-8")
  fw2_text = (cfg.vault / "frameworks" / "local-sync.md").read_text(encoding="utf-8")
  assert brief_path.stem in fw1_text
  assert brief_path.stem in fw2_text


def test_replicate_brief_includes_dialectic_trade_off_matrix_when_tensions_exist(cfg, mock_agent_step):
  """Verify that same-tier, same-domain collision produces a Dialectic Trade-off Matrix in the brief [R1+R2]."""
  _make_cognitive_framework(cfg.vault, "crdt-retention", "CRDT Retention", tier=2, domain_tags=["storage-cache"],
                            prioritize="Retaining tombstone history", over="Purging tombstones aggressively",
                            rule="Never drop tombstones")
  _make_cognitive_framework(cfg.vault, "cache-purging", "Cache Purging", tier=2, domain_tags=["storage-cache"],
                            prioritize="Purging tombstones aggressively", over="Retaining tombstone history",
                            rule="Purge after 7 days")

  run = Run(cfg, "replicate", {"frameworks": ["crdt-retention", "cache-purging"], "urls": ["https://linear.app"]})
  outputs = replicate(run, {"frameworks": ["crdt-retention", "cache-purging"], "urls": ["https://linear.app"]})

  brief_path = cfg.vault / outputs[0]
  brief_text = brief_path.read_text(encoding="utf-8")

  # Must include Dialectic Trade-off Matrix
  assert "## Dialectic Trade-off Matrix" in brief_text
  assert "### Unresolved Tensions (Human Decision Required)" in brief_text
  assert "crdt-retention" in brief_text
  assert "cache-purging" in brief_text


def test_replicate_backward_compatibility_single_framework(cfg, mock_agent_step):
  """Verify that replicate remains fully backward compatible with legacy single 'framework' argument."""
  _make_cognitive_framework(cfg.vault, "single-dogma", "Single Dogma", tier=1, domain_tags=["architecture"])

  run = Run(cfg, "replicate", {"framework": "single-dogma", "urls": ["https://linear.app"]})
  outputs = replicate(run, {"framework": "single-dogma", "urls": ["https://linear.app"]})

  brief_path = cfg.vault / outputs[0]
  assert brief_path.exists()
  brief_text = brief_path.read_text(encoding="utf-8")
  assert 'framework: "[[single-dogma]]"' in brief_text


def test_replicate_preserves_ephemeral_branch_and_head_checks(tmp_path, cfg, monkeypatch):
  """Verify that git branch isolation is enforced and moving HEAD triggers CONTRACT_VIOLATION [R1]."""
  _make_cognitive_framework(cfg.vault, "taste-fw", "Taste Framework", tier=1, domain_tags=["general"])

  # Create a clean git repo to serve as target --build repo
  repo_dir = tmp_path / "target_repo"
  repo_dir.mkdir()
  git(repo_dir, "init")
  git(repo_dir, "config", "user.email", "tester@example.com")
  git(repo_dir, "config", "user.name", "Tester")
  (repo_dir / "README.md").write_text("# Target", encoding="utf-8")
  git(repo_dir, "add", "README.md")
  git(repo_dir, "commit", "-m", "initial commit")

  # 1. Normal run: agent creates uncommitted file on the work branch
  def fake_run_agent_normal(agent, prompt, schema, **kw):
    title = schema.get("title", "")
    if title == "ui_spec":
      return AgentResult(agent, True, data=sample_ui_spec(), seconds=0.1)
    if title == "build_report":
      cwd = kw.get("cwd")
      if cwd:
        (cwd / "components").mkdir(parents=True, exist_ok=True)
        (cwd / "components" / "Nav.tsx").write_text("// nav code", encoding="utf-8")
      return AgentResult(agent, True, data=sample_build_report(), seconds=0.1)
    return AgentResult(agent, True, data={}, seconds=0.1)

  monkeypatch.setattr(steps_mod, "run_agent", fake_run_agent_normal)

  run = Run(cfg, "replicate", {"framework": "taste-fw", "urls": ["https://linear.app"], "build": str(repo_dir)})
  outputs = replicate(run, {"framework": "taste-fw", "urls": ["https://linear.app"], "build": str(repo_dir)})

  assert len(outputs) == 2
  assert "(uncommitted)" in outputs[1]

  # 2. Malicious/misbehaving agent that commits to HEAD -> triggers CONTRACT_VIOLATION
  repo_dir2 = tmp_path / "target_repo2"
  repo_dir2.mkdir()
  git(repo_dir2, "init")
  git(repo_dir2, "config", "user.email", "tester@example.com")
  git(repo_dir2, "config", "user.name", "Tester")
  (repo_dir2 / "README.md").write_text("# Target 2", encoding="utf-8")
  git(repo_dir2, "add", "README.md")
  git(repo_dir2, "commit", "-m", "initial commit")

  def fake_run_agent_commit(agent, prompt, schema, **kw):
    title = schema.get("title", "")
    if title == "ui_spec":
      return AgentResult(agent, True, data=sample_ui_spec(), seconds=0.1)
    if title == "build_report":
      cwd = kw.get("cwd")
      if cwd:
        (cwd / "malicious.txt").write_text("evil", encoding="utf-8")
        git(cwd, "add", "malicious.txt")
        git(cwd, "commit", "-m", "rogue agent commit")
      return AgentResult(agent, True, data=sample_build_report(), seconds=0.1)
    return AgentResult(agent, True, data={}, seconds=0.1)

  monkeypatch.setattr(steps_mod, "run_agent", fake_run_agent_commit)

  run2 = Run(cfg, "replicate", {"framework": "taste-fw", "urls": ["https://linear.app"], "build": str(repo_dir2)})
  with pytest.raises(PipelineError) as exc_info:
    replicate(run2, {"framework": "taste-fw", "urls": ["https://linear.app"], "build": str(repo_dir2)})

  assert exc_info.value.payload["code"] == "CONTRACT_VIOLATION"
  assert "agent committed; HEAD moved" in exc_info.value.payload["detail"]
