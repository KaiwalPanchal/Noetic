"""Shared fixtures: a throwaway vault, and schema-valid sample agent outputs."""

import json
from pathlib import Path

import pytest

from taste_engine.knowledge.config import CONFIG_NAME, Config


@pytest.fixture
def vault(tmp_path: Path) -> Path:
  v = tmp_path / "vault"
  (v / "taste-engine").mkdir(parents=True)
  (v / "frameworks").mkdir()
  (v / CONFIG_NAME).write_text(json.dumps({"owner": "Tester", "private_paths": ["Private"],
                                                     "agents": ["claude", "agy", "codex"]}), encoding="utf-8")
  return v


@pytest.fixture
def cfg(vault: Path) -> Config:
  return Config(vault, json.loads((vault / CONFIG_NAME).read_text(encoding="utf-8")))


def sample_package(slug: str = "cache-invalidation") -> dict:
  return {
      "title": "Cache invalidation is a naming problem",
      "slug": slug,
      "interest": "Systems",
      "thesis": "Most stale-cache bugs are ownership bugs.",
      "why_non_obvious": "People blame TTLs, not who owns the write path.",
      "hooks": [{"style": "contrarian", "text": "TTL is not the fix."},
                {"style": "question", "text": "Who owns the write path?"}],
      "talking_points": ["one", "two", "three"],
      "source_notes": ["Notes/cache.md"],
  }


def sample_curation() -> dict:
  return {"packages": [sample_package()],
          "rejected": [{"idea": "Hot take on tabs vs spaces", "reason": "low signal"}],
          "harness_notes": []}


def sample_framework() -> dict:
  return {
      "framework_name": "Steal Like An Artist",
      "slug": "steal-like-an-artist",
      "core_idea": "Nothing is original; remix with credit.",
      "principles": [{"name": "Steal", "explanation": "Collect influences."},
                     {"name": "Transform", "explanation": "Make it yours."}],
      "mental_moves": ["collect", "remix", "credit"],
      "when_to_apply": {"content": "posts", "code": "UI briefs", "project": "decisions"},
      "anti_patterns": ["Copying without transforming"],
      "genealogy": ["Picasso"],
      "linked_interests": ["Creativity"],
      "source": {"title": "Steal Like An Artist", "author": "Austin Kleon", "kind": "book", "url": ""},
      "provenance_note": "From the book.",
      "harness_notes": [],
  }


def sample_research() -> dict:
  return {
      "kept": [{"title": "Paper on caches", "url": "https://example.com/paper", "kind": "paper",
                "mechanism": ["write-through"], "signal_to_noise": "high",
                "genealogy": "Builds on X", "interest": "Systems", "tweet_angle": "Caches lie."}],
      "rejected": [{"title": "Fluff", "url": "https://example.com/fluff", "reason": "marketing"}],
      "package": sample_package("research-pkg"),
      "contradictions": ["Challenges stance Y"],
      "harness_notes": ["could not open the PDF"],
  }


TODAY = "2026-10-07"


def _w(path: Path, text: str) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(text, encoding="utf-8")


@pytest.fixture
def ovault(tmp_path: Path) -> Path:
  """A vault with an OverMind wiki: projects, quests, a log, and a private profile."""
  v = tmp_path / "ovault"
  (v / "taste-engine").mkdir(parents=True)
  (v / "frameworks").mkdir()
  (v / CONFIG_NAME).write_text(json.dumps({
      "owner": "Tester", "paths": {"overmind": "OverMind"}, "agents": ["claude", "codex"]}), encoding="utf-8")
  wiki = v / "OverMind" / "wiki"
  _w(wiki / "projects" / "alpha.md", """---
name: Alpha
status: active
goal: G1
competency: C1
repo: https://example.com/alpha
next_action: Ship the thing
last_touched: 2026-09-01
gate: needs review before release
---
# Alpha
""")
  _w(wiki / "projects" / "beta.md", """---
name: Beta
status: parked
goal: G2
competency: C2
next_action: Revisit later
last_touched: 2026-06-01
---
""")
  _w(wiki / "projects" / "gamma.md", "---\nname: Gamma\nstatus: active\n---\n")
  _w(wiki / "projects" / "delta.md", """---
name: Delta
status: blocked
goal: G1
next_action: Wait for vendor
last_touched: 2026-10-05
---
""")
  _w(wiki / "quests" / "QUEST-001-ship.md", "---\nstatus: open\ndue: 2026-10-01\n---\nProposed XP: 50\n")
  _w(wiki / "quests" / "QUEST-002-done.md", "---\nstatus: done\ndue: 2026-09-01\n---\n")
  _w(wiki / "quests" / "QUEST-003-later.md", "# Later\n**Status:** open\n**Due:** 2026-12-01\n")
  _w(wiki / "quests" / "XP-LEDGER.md", "not a quest")
  _w(wiki / "log" / "2026-09.md", "old month line\n")
  _w(wiki / "log" / "2026-10.md", "\n".join(f"entry {i}" for i in range(30)) + "\n")
  _w(wiki / "profile" / "secret.md", "SECRET-PROFILE-TOKEN")
  return v


@pytest.fixture
def ocfg(ovault: Path) -> Config:
  return Config(ovault, json.loads((ovault / CONFIG_NAME).read_text(encoding="utf-8")))


def private_terms():
  """Strings the owner never wants published, read from the local gitignored .private-strings.

  Empty in CI (the file is not committed), so tests using it are a local guard, not a CI guard.
  """
  f = Path(__file__).resolve().parent.parent / ".private-strings"
  if not f.exists():
    return []
  return [ln.strip().lower() for ln in f.read_text(encoding="utf-8").splitlines()
          if ln.strip() and not ln.lstrip().startswith("#")]
