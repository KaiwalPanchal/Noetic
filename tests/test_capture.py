"""Tests for workflows.capture (clip command)."""

from __future__ import annotations

from pathlib import Path
from typer.testing import CliRunner

from noetic.cli import app
from noetic.tools import clipper

runner = CliRunner()


def test_text_clip_lands_in_inbox(cfg, monkeypatch):
  monkeypatch.setattr("workflows.capture.workflow._config", lambda *a: cfg)
  res = runner.invoke(app, ["clip", "This is an important thought about system design", "--context", "System Design Idea"])
  assert res.exit_code == 0

  inbox = cfg.vault / "inbox"
  files = list(inbox.glob("*.md"))
  assert len(files) == 1
  content = files[0].read_text(encoding="utf-8")
  assert "System Design Idea" in content
  assert "This is an important thought" in content


def test_second_identical_title_does_not_overwrite(cfg, monkeypatch):
  monkeypatch.setattr("workflows.capture.workflow._config", lambda *a: cfg)
  res1 = runner.invoke(app, ["clip", "First note body", "--context", "Duplicate Title"])
  assert res1.exit_code == 0

  res2 = runner.invoke(app, ["clip", "Second note body", "--context", "Duplicate Title"])
  assert res2.exit_code == 0

  inbox = cfg.vault / "inbox"
  file1 = inbox / "duplicate-title.md"
  file2 = inbox / "duplicate-title-2.md"
  assert file1.exists()
  assert file2.exists()
  assert "First note body" in file1.read_text(encoding="utf-8")
  assert "Second note body" in file2.read_text(encoding="utf-8")


def test_http_input_calls_clip_url(cfg, monkeypatch):
  monkeypatch.setattr("workflows.capture.workflow._config", lambda *a: cfg)
  called = []

  def mock_clip_url(url, timeout=15):
    called.append(url)
    return {
      "title": "Article Title",
      "url": url,
      "content": "Article scraped content",
      "clipped_at": "2026-10-09T00:00:00",
    }

  monkeypatch.setattr(clipper, "clip_url", mock_clip_url)

  res = runner.invoke(app, ["clip", "https://example.com/article"])
  assert res.exit_code == 0
  assert called == ["https://example.com/article"]

  target_file = cfg.vault / "inbox" / "article-title.md"
  assert target_file.exists()
  assert "Article scraped content" in target_file.read_text(encoding="utf-8")
