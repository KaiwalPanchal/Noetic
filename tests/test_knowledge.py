"""Knowledge layer: note rendering/writing, context building, privacy deny-list."""

import pytest

from noetic.knowledge import context, notes
from noetic.knowledge.config import Config, slugify

from .conftest import sample_framework, sample_package, sample_research


# -- notes ----------------------------------------------------------------------

def test_frontmatter_marks_note_ai_authored_and_pending(cfg):
  fm = notes.frontmatter(cfg, "claude", "run-9", "framework", {"source": '"x"'})
  assert fm.startswith("---\nauthor: ai-agent\n")
  assert "status: pending_review" in fm and "run: run-9" in fm and 'source: "x"' in fm
  assert "pending Tester's review" in fm


def test_unique_path_and_write_never_overwrite(tmp_path):
  target = tmp_path / "sub" / "a.md"
  p1 = notes.write(target, "one")
  p2 = notes.write(target, "two")
  p3 = notes.write(target, "three")
  assert [p.name for p in (p1, p2, p3)] == ["a.md", "a-2.md", "a-3.md"]
  assert p1.read_text(encoding="utf-8") == "one"


def test_bullets_and_wikilink():
  assert notes.bullets(["a", "b"]) == "- a\n- b"
  assert notes.bullets([]) == "-" and notes.bullets([], empty="none") == "none"
  assert notes.wikilink(None, "https://x.com/a") == "https://x.com/a"
  assert notes.wikilink(None, "Notes\\cache.md") == "[[Notes/cache]]"


def test_framework_note_contents(cfg):
  path = notes.framework(cfg, sample_framework(), "claude", "r1")
  text = path.read_text(encoding="utf-8")
  assert path == cfg.frameworks / "steal-like-an-artist.md"
  for needle in ("## Core Idea", "1. **Steal**: Collect influences.", "3. credit",
                 "[[interests#Creativity]]", "Austin Kleon", "## Applications Log"):
    assert needle in text


def test_source_note_links_back_to_framework(cfg):
  d = sample_framework()
  fw = notes.framework(cfg, d, "claude", "r1")
  src = notes.source_note(cfg, d, fw, "claude", "r1")
  assert src.parent == cfg.frameworks / "sources"
  assert "[[steal-like-an-artist]]" in src.read_text(encoding="utf-8")


def test_curation_numbering_increments_and_ignores_malformed_files(cfg):
  folder = cfg.engine / "03-pipeline" / "01-curation"
  folder.mkdir(parents=True)
  (folder / "curation-007-old.md").write_text("x", encoding="utf-8")
  (folder / "curation-abc-bad.md").write_text("x", encoding="utf-8")
  assert notes.next_curation_number(cfg) == 8
  path = notes.curation_package(cfg, sample_package(), "claude", "r")
  assert path.name == "curation-008-cache-invalidation.md"
  text = path.read_text(encoding="utf-8")
  assert "### Angle A: Contrarian" in text and "### Angle B: Question" in text and "[[Notes/cache]]" in text


def test_rejected_section(cfg):
  assert notes.rejected_section([]) == ""
  out = notes.rejected_section([{"idea": "i", "reason": "r"}])
  assert "| i |  | r |" in out
  out = notes.rejected_section([{"title": "T", "url": "u", "reason": "r"}], key="title")
  assert "| T | u | r |" in out


def test_signal_goes_to_kind_specific_folder(cfg):
  s = sample_research()["kept"][0]
  path = notes.signal(cfg, s, "agy", "r")
  assert path.parent == cfg.engine / "02-signals" / "papers"
  assert "**Signal-to-noise:** high" in path.read_text(encoding="utf-8")


def test_append_application_fills_placeholder_then_appends(cfg, tmp_path):
  fw = notes.framework(cfg, sample_framework(), "claude", "r")
  out1 = cfg.vault / "out-one.md"
  out2 = cfg.vault / "out-two.md"
  notes.append_application(fw, "code", out1)
  notes.append_application(fw, "content", out2)
  text = fw.read_text(encoding="utf-8")
  assert text.index("[[out-one]]") < text.index("[[out-two]]")
  assert "## Applications Log\n-\n" not in text
  notes.append_application(tmp_path / "missing.md", "code", out1)  # no-op, no error


def test_append_application_adds_section_when_absent(tmp_path):
  f = tmp_path / "fw.md"
  f.write_text("# Just a note\n", encoding="utf-8")
  notes.append_application(f, "project", tmp_path / "o.md")
  assert "## Applications Log" in f.read_text(encoding="utf-8")


def test_set_status_replaces_previous_review_fields(cfg):
  path = notes.framework(cfg, sample_framework(), "claude", "r")
  notes.set_status(path, "approved", "ok")
  notes.set_status(path, "rejected")
  text = path.read_text(encoding="utf-8")
  assert text.count("status:") == 1 and "status: rejected" in text and "review_note" not in text
  assert "# Framework: Steal Like An Artist" in text


# -- config ---------------------------------------------------------------------

def test_slugify():
  assert slugify("  Hello, World! _ Foo--Bar ") == "hello-world-foo-bar"


def test_config_defaults_and_overrides(vault):
  c = Config(vault, {"agents": {"ingest": "codex"}, "paths": {"twitter": "X"}, "x_char_limit": "400"})
  assert c.agent_order("ingest") == ["codex"] and c.agent_order("curate") == []  # no hardcoded default
  assert c.twitter == vault / "X" and c.x_char_limit == 400
  assert c.state_dir == vault / ".taste-engine"
  assert c.overmind is None


# -- context --------------------------------------------------------------------

def test_read_body_strips_frontmatter_callout_and_truncates(tmp_path):
  f = tmp_path / "n.md"
  f.write_text("---\na: b\n---\n> [!NOTE] auto\nreal content " + "x" * 100, encoding="utf-8")
  body = context.read_body(f, 20)
  assert body.startswith("real content") and "a: b" not in body and "[!NOTE]" not in body
  assert body.endswith("[truncated]")


def test_is_private_matches_folder_and_exact_path(cfg):
  assert context.is_private(cfg, cfg.vault / "Private" / "x.md")
  assert context.is_private(cfg, cfg.vault / "private")  # case-insensitive
  assert not context.is_private(cfg, cfg.vault / "PrivateButNot" / "x.md")


def test_iter_notes_skips_private_and_tooling_dirs(cfg):
  for rel in ("Private/a.md", ".obsidian/b.md", ".git/c.md", "ok/d.md", "e.md"):
    p = cfg.vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x", encoding="utf-8")
  names = sorted(p.name for p in context.iter_notes(cfg))
  assert names == ["d.md", "e.md"]


def test_search_ranks_by_term_hits_and_filename_and_handles_empty(cfg):
  (cfg.vault / "caching.md").write_text("caching caching caching notes", encoding="utf-8")
  (cfg.vault / "other.md").write_text("one caching mention", encoding="utf-8")
  (cfg.vault / "unrelated.md").write_text("nothing here", encoding="utf-8")
  out = context.search(cfg, ["caching"])
  assert out.index("caching.md") < out.index("other.md") and "unrelated" not in out
  assert context.search(cfg, ["ab"]) == "(no search terms)"
  assert context.search(cfg, ["zzzzzz"]) == "(nothing relevant found in the vault)"


def test_search_skips_pipeline_outputs_and_private(cfg):
  out_dir = cfg.engine / "03-pipeline" / "01-curation"
  out_dir.mkdir(parents=True)
  (out_dir / "curation-001-x.md").write_text("caching generated", encoding="utf-8")
  (cfg.vault / "Private").mkdir()
  (cfg.vault / "Private" / "p.md").write_text("caching private", encoding="utf-8")
  assert context.search(cfg, ["caching"]) == "(nothing relevant found in the vault)"


def test_resolve_vault_path_exact_unique_partial_and_ambiguous(cfg):
  (cfg.vault / "Reading").mkdir()
  (cfg.vault / "Reading" / "make-it-stick.md").write_text("x", encoding="utf-8")
  (cfg.vault / "a-note-1.md").write_text("x", encoding="utf-8")
  (cfg.vault / "a-note-2.md").write_text("x", encoding="utf-8")
  assert context.resolve_vault_path(cfg, "Reading/make-it-stick.md").name == "make-it-stick.md"
  assert context.resolve_vault_path(cfg, "Reading/make-it-stick").name == "make-it-stick.md"
  assert context.resolve_vault_path(cfg, "stick").name == "make-it-stick.md"
  assert context.resolve_vault_path(cfg, "a-note") is None  # ambiguous
  assert context.resolve_vault_path(cfg, "nope-nothing") is None


def test_interests_taste_frameworks_helpers(cfg):
  assert "no interests.md" in context.interests(cfg)
  assert context.interest_names(cfg) == []
  assert context.taste(cfg) == "(no stances or filters yet)"
  assert context.frameworks(cfg) == "(none yet)"
  (cfg.engine / "interests.md").write_text("## Systems\nstuff\n## Design\nmore\n", encoding="utf-8")
  stance = cfg.engine / "01-taste-graph" / "stances"
  stance.mkdir(parents=True)
  (stance / "s1.md").write_text("Prefer boring tech.", encoding="utf-8")
  notes.framework(cfg, sample_framework(), "claude", "r")
  assert context.interest_names(cfg) == ["Systems", "Design"]
  assert "stance: s1" in context.taste(cfg) and "Prefer boring tech." in context.taste(cfg)
  assert "steal-like-an-artist: Nothing is original" in context.frameworks(cfg)


def test_archive_lists_published_titles(cfg):
  assert context.archive(cfg) == "(nothing published yet)"
  arch = cfg.engine / "03-pipeline" / "04-archive"
  arch.mkdir(parents=True)
  (arch / "old-post.md").write_text("x", encoding="utf-8")
  (arch / "README.md").write_text("x", encoding="utf-8")
  assert context.archive(cfg) == "- old-post"
