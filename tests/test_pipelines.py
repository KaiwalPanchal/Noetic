"""End-to-end pipeline runs with a scripted agent (no CLI, no network).

Tests:
1. Two-step ingestion: extract (tools=[]) -> build_framework -> write [Phase 2, R1, R2]
2. Cache key calculation and resume behavior [R1]
3. Rejection handling (clean abort and status=rejected) [R1]
4. Non-clobbering merge protecting approved notes and human edits [R1+R2]
5. Applications Log appending inside machine markers [R2]
6. Hard per-run budget ceiling enforcement [R1]
7. Master Table update strictly within designated markers [R2]
"""

import hashlib
import json
from pathlib import Path
import pytest

from noetic.agents.runners import AgentResult
from noetic.gates import gate
from noetic.knowledge import notes
from noetic.knowledge.dedup import core_semantic_text
from noetic.orchestration import steps as steps_mod
from noetic.orchestration.run import PipelineError, Run
from workflows.taste_engine.pipelines import curate as curate_mod
from workflows.taste_engine.pipelines import research as research_mod
from workflows.taste_engine.pipelines.curate import curate
from workflows.taste_engine.pipelines.ingest import ingest
from workflows.taste_engine.pipelines.replicate import replicate
from workflows.taste_engine.pipelines.research import dead_links, research

from .conftest import sample_curation, sample_framework, sample_research


@pytest.fixture
def agent_returns(monkeypatch):
  """agent_returns(data) makes agent calls succeed; returns the call log."""
  calls = []

  def install(data):
    queue = list(data) if isinstance(data, list) else None

    def fake(agent, prompt, schema, **kw):
      calls.append({"agent": agent, "prompt": prompt, "schema": schema, "kw": kw})
      if queue is not None:
        item = queue.pop(0) if queue else {}
        return AgentResult(agent, True, data=item, seconds=0.1)

      s_title = schema.get("title", "")
      if s_title == "extraction" and "entities" not in data:
        extract_data = {
          "schema_version": "1.0.0",
          "title": data.get("framework_name", "Extracted Title"),
          "source_metadata": data.get("source", {"title": "Title", "author": "Author", "kind": "book", "url": ""}),
          "entities": ["Remixing", "Influence"],
          "core_principles": [
            {"name": p.get("name", "Principle"), "description": p.get("explanation", "Description")}
            if isinstance(p, dict) else {"name": "Principle", "description": str(p)}
            for p in data.get("principles", [])
          ] or [{"name": "Steal", "description": "Collect influences"}],
          "mental_moves": data.get("mental_moves", ["collect", "remix"]),
          "anti_patterns": [
            {"trap_name": "Copying", "symptom": "Plagiarism", "failure_mechanism": "No transformation", "recovery_move": "Remix"}
          ],
          "genealogy": data.get("genealogy", ["Picasso"]),
          "rejected": False,
          "rejection_reason": "",
          "is_signal": True,
          "harness_notes": [],
        }
        return AgentResult(agent, True, data=extract_data, seconds=0.1)

      if s_title == "cognitive_framework" and "ontology" not in data:
        cog_data = {
          "schema_version": "1.0.0",
          "framework_name": data.get("framework_name", "Framework"),
          "slug": data.get("slug", "framework"),
          "source": data.get("source", {"title": "Title", "author": "Author", "kind": "book", "url": ""}),
          "ontology": {
            "domain": "Creative Strategy",
            "primitives": [{"name": "Remix", "kind": "entity", "definition": "Combining influences", "observable_indicator": "Novel output"}],
            "governing_invariant": "Nothing is completely original",
          },
          "directional_heuristics": [
            {
              "context": "When building new creative work",
              "prioritize": "Stealing and transforming diverse influences",
              "over": "Trying to invent from a blank vacuum",
              "because": "All creativity builds on prior foundations",
              "operational_rule": "Collect 10 references before designing",
              "tier": 1,
              "domain_tags": ["creativity", "strategy"],
              "provenance_anchor": "Austin Kleon Chapter 1",
            }
          ],
          "trade_off_matrix": [
            {
              "dimension": "Originality vs Proven Mechanics",
              "recommended_choice": "Proven mechanics transformed",
              "sacrificed": "Total novelty",
              "gained": "Reliable execution",
              "boundary_flip_condition": "Foundational paradigm invention",
            }
          ],
          "anti_patterns": [
            {
              "trap_name": "Shallow Knockoff",
              "symptom": "Copying without understanding",
              "failure_mechanism": "Misses internal mechanism",
              "recovery_move": "Transform into own expression",
            }
          ],
          "evaluation_rubric": {
            "the_keyboard_test": "References folder exists on disk before coding begins.",
            "admission_test_scores": {
              "executable_heuristic": 5,
              "cognitive_compression": 5,
              "keyboard_test": 5,
              "explicit_failure_mode": 4,
              "cross_domain_transfer": 4,
            },
            "falsification_criteria": "If work created in isolation beats influence collection.",
          },
          "faithful_layer": {
            "core_idea": data.get("core_idea", "Remix with credit"),
            "razor": "Credit everything you steal",
            "mental_moves": data.get("mental_moves", ["collect", "credit"]),
          },
          "applied_layer": {
            "linked_interests": data.get("linked_interests", ["Creativity"]),
            "stance_alignments": ["Iterative Building"],
            "stance_conflicts": ["Genius Myth"],
          },
          "genealogy": data.get("genealogy", ["Picasso"]),
          "harness_notes": [],
        }
        return AgentResult(agent, True, data=cog_data, seconds=0.1)

      return AgentResult(agent, True, data=data, seconds=0.1)

    monkeypatch.setattr(steps_mod, "run_agent", fake)
    return calls
  return install


def front(path):
  return path.read_text(encoding="utf-8")


def test_ingest_two_step(cfg, agent_returns):
  """Verify ingest runs as extract (tools=[]) -> build_framework -> write [P2, R1, R2]."""
  note = cfg.vault / "Reading" / "kleon.md"
  note.parent.mkdir(parents=True, exist_ok=True)
  note.write_text("---\ntags: x\n---\nSteal like an artist notes about remixing.", encoding="utf-8")
  calls = agent_returns(sample_framework())

  run = Run(cfg, "ingest", {"source": "Reading/kleon.md"})
  outputs = ingest(run, {"source": "Reading/kleon.md"})

  assert len(outputs) == 2
  assert len(calls) == 2

  # Step 1: extract call invariants
  assert calls[0]["schema"]["title"] == "extraction"
  assert calls[0]["kw"]["tools"] == []
  assert calls[0]["kw"]["web"] is False
  assert "remixing" in calls[0]["prompt"] and "tags: x" not in calls[0]["prompt"]

  # Step 2: build_framework call invariants
  assert calls[1]["schema"]["title"] == "cognitive_framework"
  assert calls[1]["kw"]["web"] is False

  # Outputs
  fw = cfg.vault / outputs[0]
  assert fw.parent == cfg.frameworks and "steal-like-an-artist" in fw.name
  text = front(fw)
  assert "status: pending_review" in text
  assert "# Framework: Steal Like An Artist" in text
  assert "<!-- NOETIC:AUTO:START -->" in text and "<!-- NOETIC:AUTO:END -->" in text
  assert "<!-- NOETIC:LOG:START -->" in text and "<!-- NOETIC:LOG:END -->" in text
  assert (cfg.vault / outputs[1]).parent.name == "sources"


def test_ingest_rejected_source_aborts_cleanly(cfg, monkeypatch):
  """If Step 1 extraction returns rejected: true, pipeline aborts cleanly with logged reason [R1]."""
  rejected_data = {
    "schema_version": "1.0.0",
    "title": "Marketing Fluff Hype",
    "source_metadata": {"title": "Hype", "author": "Influencer", "kind": "url", "url": "https://example.com/hype"},
    "entities": [],
    "core_principles": [],
    "mental_moves": [],
    "anti_patterns": [],
    "genealogy": [],
    "rejected": True,
    "rejection_reason": "Marketing hype slop without operational mechanics",
    "is_signal": False,
    "harness_notes": [],
  }

  calls = []
  def fake(agent, prompt, schema, **kw):
    calls.append(schema["title"])
    return AgentResult(agent, True, data=rejected_data, seconds=0.1)

  monkeypatch.setattr(steps_mod, "run_agent", fake)

  run = Run(cfg, "ingest", {"source": "https://example.com/hype"})
  outputs = ingest(run, {"source": "https://example.com/hype"})

  assert outputs == []
  assert len(calls) == 1  # Step 2 never ran
  assert run.state["status"] == "rejected"
  assert "Marketing hype slop" in run.state["rejection_reason"]


def test_ingest_resume_skips_step1_when_cache_key_unchanged(cfg, agent_returns):
  """Resume skips Step 1 if cache key is unchanged; re-runs when key changes [R1]."""
  note = cfg.vault / "Reading" / "kleon.md"
  note.parent.mkdir(parents=True, exist_ok=True)
  note.write_text("Steal like an artist initial text.", encoding="utf-8")
  calls = agent_returns(sample_framework())

  # Run 1: initial run finishes extract and build_framework
  run1 = Run(cfg, "ingest", {"source": "Reading/kleon.md"})
  run1_id = run1.id
  ingest(run1, {"source": "Reading/kleon.md"})
  assert len(calls) == 2  # extract (1) + build_framework (2)
  extract_calls = [c for c in calls if c["schema"]["title"] == "extraction"]
  assert len(extract_calls) == 1

  # Run 2: resume with UNCHANGED source note -> Step 1 extract is skipped
  run2 = Run(cfg, "ingest", {"source": "Reading/kleon.md"}, run_id=run1_id)
  ingest(run2, {"source": "Reading/kleon.md"})
  extract_calls_after_resume = [c for c in calls if c["schema"]["title"] == "extraction"]
  assert len(extract_calls_after_resume) == 1  # extract was reused from cache!

  # Run 3: change source note body -> cache key changes, Step 1 extract re-runs!
  note.write_text("Completely rewritten note content altering source hash.", encoding="utf-8")
  run3 = Run(cfg, "ingest", {"source": "Reading/kleon.md"}, run_id=run1_id)
  ingest(run3, {"source": "Reading/kleon.md"})
  extract_calls_after_change = [c for c in calls if c["schema"]["title"] == "extraction"]
  assert len(extract_calls_after_change) == 2  # extract re-ran due to cache invalidation


def test_human_edits_survive_reingest_and_merge(cfg, agent_returns):
  """Human edits made to approved framework notes survive subsequent re-ingest runs [R1+R2]."""
  agent_returns(sample_framework())

  # Ingest once
  run1 = Run(cfg, "ingest", {"source": "Austin Kleon Book"})
  outputs = ingest(run1, {"source": "Austin Kleon Book"})
  fw_path = cfg.vault / outputs[0]

  # Human approves the note
  gate.approve(fw_path, "Looks solid")
  assert gate.status_of(fw_path) == "approved"
  assert notes.get_approval_hash(fw_path) is not None

  # Human appends custom notes OUTSIDE the machine-managed markers
  human_addition = "\n\n## Custom Implementation Notes\n- Use only for frontend UI components in Q4.\n- Never use for backend database migrations.\n"
  fw_path.write_text(fw_path.read_text(encoding="utf-8") + human_addition, encoding="utf-8")

  # Second ingest triggers Tier 1 slug match (MERGE)
  run2 = Run(cfg, "ingest", {"source": "Austin Kleon Book"})
  outputs2 = ingest(run2, {"source": "Austin Kleon Book"})

  merged_text = fw_path.read_text(encoding="utf-8")

  # Invariants:
  # 1. Target file was NOT overwritten in place
  # 2. Status is moved to needs_merge_review
  # 3. Proposed enrichment is written inside <!-- NOETIC:PROPOSED:START -->
  # 4. Human custom notes survived completely intact!
  assert "status: needs_merge_review" in merged_text
  assert "<!-- NOETIC:PROPOSED:START -->" in merged_text
  assert "### Proposed Enrichment" in merged_text
  assert "## Custom Implementation Notes" in merged_text
  assert "Never use for backend database migrations." in merged_text


def test_human_edits_survive_applications_log_append(cfg):
  """Applications log appends strictly inside <!-- NOETIC:LOG:START --> without clobbering human edits [R2]."""
  d = sample_framework()
  fw_path = notes.framework(cfg, d, "claude", "run1")

  # Human adds notes
  human_text = "\n\n## Personal Reflection\nOriginal thought on artist stealing.\n"
  fw_path.write_text(fw_path.read_text(encoding="utf-8") + human_text, encoding="utf-8")

  # Append two applications
  notes.append_application(fw_path, "code", cfg.vault / "project-a.md")
  notes.append_application(fw_path, "writing", cfg.vault / "essay-b.md")

  text = fw_path.read_text(encoding="utf-8")
  assert "[[project-a]]" in text
  assert "[[essay-b]]" in text
  assert text.index("<!-- NOETIC:LOG:START -->") < text.index("[[project-a]]") < text.index("<!-- NOETIC:LOG:END -->")
  assert "## Personal Reflection" in text
  assert "Original thought on artist stealing." in text


def test_master_table_mutates_only_designated_table_rows(cfg, agent_returns):
  """Master Table in frameworks/README.md updates strictly between TABLE markers [R2]."""
  readme = cfg.frameworks / "README.md"
  readme.parent.mkdir(parents=True, exist_ok=True)
  initial_readme = """# The Knowledgebase Framework Bar

> **Prime Directive:** Taste is subtraction.

## Custom Section Preceding Table
This section must never be touched or clobbered.

## Master Frameworks Catalog

<!-- NOETIC:TABLE:START -->
| Framework | Slug | Status | Domain | Admission Score | Source |
|---|---|---|---|---|---|
<!-- NOETIC:TABLE:END -->

## Epilogue Section Post Table
This epilogue must also remain perfectly preserved.
"""
  readme.write_text(initial_readme, encoding="utf-8")

  agent_returns(sample_framework())
  ingest(Run(cfg, "ingest", {"source": "Austin Kleon Book"}), {"source": "Austin Kleon Book"})

  updated_readme = readme.read_text(encoding="utf-8")
  assert "## Custom Section Preceding Table" in updated_readme
  assert "This section must never be touched or clobbered." in updated_readme
  assert "## Epilogue Section Post Table" in updated_readme
  assert "This epilogue must also remain perfectly preserved." in updated_readme
  assert "steal-like-an-artist" in updated_readme
  assert "| [[steal-like-an-artist|" in updated_readme


def test_budget_hard_stop_halts_execution_on_limit_breach(cfg, monkeypatch):
  """Hard token/cost budget ceiling per run is enforced [R1]."""
  cfg.budget["per_run_usd"] = 0.50

  def expensive_agent(agent, prompt, schema, **kw):
    return AgentResult(agent, True, data=sample_framework(), seconds=0.5, cost_usd=0.75)

  monkeypatch.setattr(steps_mod, "run_agent", expensive_agent)

  run = Run(cfg, "ingest", {"source": "Expensive Run"})
  with pytest.raises(PipelineError) as exc:
    ingest(run, {"source": "Expensive Run"})

  assert exc.value.payload["code"] == "BUDGET_EXCEEDED"
  assert run.state["status"] == "failed"


def test_ingest_url_enables_web_and_book_title_falls_back_to_vault_search(cfg, agent_returns):
  calls = agent_returns(sample_framework())
  ingest(Run(cfg, "ingest", {"source": "https://example.com/post"}), {"source": "https://example.com/post"})
  assert calls[0]["kw"]["web"] is True and "https://example.com/post" in calls[0]["prompt"]

  ingest(Run(cfg, "ingest", {"source": "Some Book Title"}), {"source": "Some Book Title"})
  assert calls[2]["kw"]["web"] is False and "book/topic title: Some Book Title" in calls[2]["prompt"]


def test_curate_writes_numbered_packages_with_rejected_table(cfg, agent_returns):
  (cfg.vault / "Notes").mkdir(parents=True, exist_ok=True)
  (cfg.vault / "Notes" / "cache.md").write_text("Cache invalidation is hard. Caching caching.", encoding="utf-8")
  calls = agent_returns(sample_curation())

  run = Run(cfg, "curate", {"focus": "caching"})
  outputs = curate(run, {"focus": "caching"})

  assert len(outputs) == 1 and "curation-001-" in outputs[0]
  text = front(cfg.vault / outputs[0])
  assert "## Rejected (taste stays visible)" in text and "Hot take on tabs vs spaces" in text
  assert "Notes/cache.md" in calls[0]["prompt"]

  again = curate(Run(cfg, "curate", {"focus": "caching"}), {"focus": "caching"})
  assert "curation-002-" in again[0]


def test_curate_never_feeds_private_paths_to_the_model(cfg, agent_returns):
  (cfg.vault / "Private").mkdir(parents=True, exist_ok=True)
  (cfg.vault / "Private" / "diary.md").write_text("caching secret diary entry", encoding="utf-8")
  (cfg.vault / "Public.md").write_text("caching public note", encoding="utf-8")
  calls = agent_returns(sample_curation())
  curate(Run(cfg, "curate", {"focus": "caching"}), {"focus": "caching"})
  assert "secret diary" not in calls[0]["prompt"] and "public note" in calls[0]["prompt"]


def test_curate_respects_forced_agent(cfg, agent_returns):
  calls = agent_returns(sample_curation())
  curate(Run(cfg, "curate", {}), {"focus": "x", "agent": "agy"})
  assert calls[0]["agent"] == "agy"


def test_research_writes_signals_package_and_flags_dead_links(cfg, agent_returns, monkeypatch):
  monkeypatch.setattr(research_mod, "url_ok", lambda url: "fluff" not in url)
  data = sample_research()
  calls = agent_returns(data)

  run = Run(cfg, "research", {"topic": "caches"})
  outputs = research(run, {"topic": "caches"})

  assert any("02-signals" in o and "papers" in o for o in outputs)
  pkg = [o for o in outputs if "01-curation" in o][0]
  text = front(cfg.vault / pkg)
  assert "URL unverified" in text
  assert "Challenges to existing stances" in text and "Challenges stance Y" in text
  assert calls[0]["kw"]["web"] is True and calls[0]["kw"]["timeout"] == 1500
  assert any("could not open the PDF" in n for n in run.notes)


def test_research_retries_when_a_kept_url_is_dead(cfg, monkeypatch):
  seen = []
  results = iter([sample_research(), sample_research()])

  def fake(agent, prompt, schema, **kw):
    seen.append(prompt)
    return AgentResult(agent, True, data=next(results), seconds=0.1)
  monkeypatch.setattr(steps_mod, "run_agent", fake)
  alive = iter([False, True, True, True, True, True])
  monkeypatch.setattr(research_mod, "url_ok", lambda url: next(alive))
  research(Run(cfg, "research", {"topic": "t"}), {"topic": "t"})
  assert len(seen) == 2 and "does not resolve" in seen[1]


def test_dead_links_reports_only_kept_sources(monkeypatch):
  monkeypatch.setattr(research_mod, "url_ok", lambda url: url.endswith("good"))
  d = {"kept": [{"url": "https://a/good"}, {"url": "https://a/bad"}]}
  problems = dead_links(d)
  assert len(problems) == 1 and "https://a/bad" in problems[0]


def test_replicate_unknown_framework_fails_with_suggestions(cfg, agent_returns):
  (cfg.frameworks / "steal-like-an-artist.md").write_text("# fw", encoding="utf-8")
  calls = agent_returns({})
  run = Run(cfg, "replicate", {"framework": "steal-everything"})
  with pytest.raises(PipelineError) as exc:
    replicate(run, {"framework": "steal-everything", "urls": ["https://a.com"]})
  assert exc.value.payload["code"] == "FRAMEWORK_NOT_FOUND"
  assert exc.value.payload["did_you_mean"] == ["steal-like-an-artist"]
  assert calls == []
