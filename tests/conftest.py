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
  (v / CONFIG_NAME).write_text(json.dumps({"owner": "Tester", "private_paths": ["Private"]}), encoding="utf-8")
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
