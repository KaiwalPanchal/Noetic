"""End-to-end pipeline runs with a scripted agent (no CLI, no network)."""

import pytest

from noetic.orchestration import steps as steps_mod
from noetic.orchestration.run import PipelineError, Run
from workflows.taste_engine.pipelines import curate as curate_mod
from workflows.taste_engine.pipelines import research as research_mod
from workflows.taste_engine.pipelines.curate import curate
from workflows.taste_engine.pipelines.ingest import ingest
from workflows.taste_engine.pipelines.replicate import replicate
from workflows.taste_engine.pipelines.research import dead_links, research
from noetic.agents.runners import AgentResult

from .conftest import sample_curation, sample_framework, sample_research


@pytest.fixture
def agent_returns(monkeypatch):
  """agent_returns(data) makes every agent call succeed with `data`; returns the call log."""
  calls = []

  def install(data):
    def fake(agent, prompt, schema, **kw):
      calls.append({"agent": agent, "prompt": prompt, "kw": kw})
      return AgentResult(agent, True, data=data, seconds=0.1)
    monkeypatch.setattr(steps_mod, "run_agent", fake)
    return calls
  return install


def front(path):
  return path.read_text(encoding="utf-8")


def test_ingest_vault_note_writes_framework_and_source_pending_review(cfg, agent_returns):
  note = cfg.vault / "Reading" / "kleon.md"
  note.parent.mkdir()
  note.write_text("---\ntags: x\n---\nSteal like an artist notes about remixing.", encoding="utf-8")
  calls = agent_returns(sample_framework())

  run = Run(cfg, "ingest", {"source": "Reading/kleon.md"})
  outputs = ingest(run, {"source": "Reading/kleon.md"})

  assert len(outputs) == 2
  fw = cfg.vault / outputs[0]
  assert fw.parent == cfg.frameworks and "steal-like-an-artist" in fw.name
  text = front(fw)
  assert "status: pending_review" in text and "# Framework: Steal Like An Artist" in text
  assert (cfg.vault / outputs[1]).parent.name == "sources"
  # the note body (minus frontmatter) reached the model; the agent was not given web access
  assert "remixing" in calls[0]["prompt"] and "tags: x" not in calls[0]["prompt"]
  assert calls[0]["kw"]["web"] is False


def test_ingest_url_enables_web_and_book_title_falls_back_to_vault_search(cfg, agent_returns):
  calls = agent_returns(sample_framework())
  ingest(Run(cfg, "ingest", {"source": "https://example.com/post"}), {"source": "https://example.com/post"})
  assert calls[0]["kw"]["web"] is True and "https://example.com/post" in calls[0]["prompt"]

  ingest(Run(cfg, "ingest", {"source": "Some Book Title"}), {"source": "Some Book Title"})
  assert calls[1]["kw"]["web"] is False and "book/topic title: Some Book Title" in calls[1]["prompt"]


def test_ingest_never_overwrites_an_existing_framework(cfg, agent_returns):
  agent_returns(sample_framework())
  a = ingest(Run(cfg, "ingest", {"source": "Book"}), {"source": "Book"})
  b = ingest(Run(cfg, "ingest", {"source": "Book"}), {"source": "Book"})
  assert a[0] != b[0] and (cfg.vault / a[0]).exists() and (cfg.vault / b[0]).exists()


def test_curate_writes_numbered_packages_with_rejected_table(cfg, agent_returns):
  (cfg.vault / "Notes").mkdir()
  (cfg.vault / "Notes" / "cache.md").write_text("Cache invalidation is hard. Caching caching.", encoding="utf-8")
  calls = agent_returns(sample_curation())

  run = Run(cfg, "curate", {"focus": "caching"})
  outputs = curate(run, {"focus": "caching"})

  assert len(outputs) == 1 and "curation-001-" in outputs[0]
  text = front(cfg.vault / outputs[0])
  assert "## Rejected (taste stays visible)" in text and "Hot take on tabs vs spaces" in text
  assert "Notes/cache.md" in calls[0]["prompt"]  # vault search results were put in context

  again = curate(Run(cfg, "curate", {"focus": "caching"}), {"focus": "caching"})
  assert "curation-002-" in again[0]


def test_curate_never_feeds_private_paths_to_the_model(cfg, agent_returns):
  (cfg.vault / "Private").mkdir()
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
  assert "URL unverified" in text  # rejected source with a dead URL is annotated
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
  alive = iter([False, True, True, True, True, True])  # first dead_links check sees a dead kept URL
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
  assert calls == []  # fails before spending any agent call
