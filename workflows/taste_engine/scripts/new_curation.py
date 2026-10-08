"""Taste Engine scaffolder.

Creates stances, signals, frameworks, thread drafts and journey entries inside
the vault, with authorship attribution (AI agent vs. human owner). Paths and
names come from `taste-engine.config.json` (see te_config.py).

Examples:
  python new_curation.py framework "Steal Like an Artist" --source "Austin Kleon (2012)"
  python new_curation.py signal "Graphiti temporal edges" --type repo
  python new_curation.py journey "Shipped the install script"
  python new_curation.py draft "Why agent memory is broken" --author owner
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from overmind.knowledge.config import Config, frontmatter, load_config, slugify, today  # noqa: E402

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
  sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
  sys.stderr.reconfigure(encoding="utf-8")


def _write(target: Path, content: str, author: str) -> None:
  if target.exists():
    print(f"Error: File already exists: {target}")
    sys.exit(1)
  target.parent.mkdir(parents=True, exist_ok=True)
  target.write_text(content, encoding="utf-8")
  print(f"✓ Created {target} (Author: {author})")


def create_stance(cfg: Config, title: str, author: str):
  content = f"""{frontmatter(cfg, author)}# Stance: {title}

**Type:** Conviction · **Tags:** #taste-filter #stance
**Related:**

---

## The Thesis

State the core conviction clearly and without hedging.

---

## Why the Common Approach Fails

Explain why the default approach breaks, degrades quality, or compounds noise.

---

## The Better Pattern

Provide the alternative mechanism, guardrail, or mental model.
"""
  _write(cfg.engine / "01-taste-graph" / "stances" / f"{slugify(title)}.md", content, author)


def create_signal(cfg: Config, title: str, signal_type: str, author: str):
  folder = {"paper": "papers", "repo": "repos", "postmortem": "postmortems", "web": "web"}[signal_type]
  content = f"""{frontmatter(cfg, author)}# Signal: {title}

**Category:** {signal_type.capitalize()} · **Tags:** #signal #{signal_type}
**Source URL:**

---

## Core Mechanism (3 Bullets)
-
-
-

## The Curation Judgment (Taste Filter)
- **Signal-to-Noise Ratio:** High / Medium / Low
- **Passes Negative Filters?** Yes / No (which one, and why)
- **Genealogy / Influences:** What older idea is this a remix of?
- **Linked Interests:**

## Extracted Tweet Angle / Hook
>
"""
  _write(cfg.engine / "02-signals" / folder / f"{slugify(title)}.md", content, author)


def create_framework(cfg: Config, title: str, source: str, author: str):
  content = f"""{frontmatter(cfg, author, {"type": "framework", "source": f'"{source}"', "applies-to": "[content, code, project]"})}# Framework: {title}

**Source:** {source}
**Linked Interests:**
**Tags:** #framework

---

## Core Idea
One or two sentences: the whole framework compressed.

## Principles
1.

## Mental Moves / Procedures
Repeatable steps you can actually execute. Write them as verbs.
1.

## When to Apply
- **Content:**
- **Code:**
- **Projects / Decisions:**

## Anti-Patterns
What misusing this framework looks like.
-

## Source Genealogy
Where the author stole it from, and what it remixes.
-

## Applications Log
Dated links to briefs, curation packages and decisions that used this framework.
-
"""
  _write(cfg.frameworks / f"{slugify(title)}.md", content, author)


def create_draft(cfg: Config, title: str, author: str):
  content = f"""{frontmatter(cfg, author)}# Thread Draft: {title}

**Status:** In Progress · **Tags:** #twitter-thread #draft
**Source Curation:**
**Linked Stance / Framework:**

---

### Tweet 1 (The Hook)
[Hook here - max {cfg.x_char_limit} chars]

---

### Tweet 2 (The Problem / Context)
[Problem statement]

---

### Tweet 3 (The Core Mechanism)
[Mechanism / code / diagram]

---

### Tweet 4 (The Trade-offs / Gotchas)
[Honest trade-offs]

---

### Tweet 5 (Summary / CTA)
[Takeaway + question]
"""
  _write(cfg.engine / "03-pipeline" / "02-drafts" / f"{slugify(title)}.md", content, author)


def create_journey(cfg: Config, title: str, author: str):
  content = f"""{frontmatter(cfg, author, {"type": "journey"})}# Journey {today()}: {title}

## What I built

## What broke / surprised me

## The decision (and why)

## Proof
Links, screenshots, commits.

## Tweet candidates

### Tweet 1
"""
  _write(cfg.twitter / "journey" / f"{today()}-{slugify(title)}.md", content, author)


def main():
  parent = argparse.ArgumentParser(add_help=False)
  parent.add_argument(
    "--author", default="ai-agent",
    help="'ai-agent' (default) or the human author's name; 'owner' uses the configured owner",
  )

  parser = argparse.ArgumentParser(description="Scaffold Taste Engine notes", parents=[parent])
  sub = parser.add_subparsers(dest="command")

  sub.add_parser("stance", help="New stance note", parents=[parent]).add_argument("title")

  p = sub.add_parser("signal", help="New signal note", parents=[parent])
  p.add_argument("title")
  p.add_argument("--type", choices=["paper", "repo", "postmortem", "web"], default="paper")

  p = sub.add_parser("framework", help="New framework note", parents=[parent])
  p.add_argument("title")
  p.add_argument("--source", default="", help="Book, author, URL")

  sub.add_parser("draft", help="New thread draft", parents=[parent]).add_argument("title")
  sub.add_parser("journey", help="New build-in-public journey entry", parents=[parent]).add_argument("title")

  args = parser.parse_args()
  if not args.command:
    parser.print_help()
    return

  cfg = load_config()
  author = slugify(cfg.owner) if args.author == "owner" else args.author

  if args.command == "stance":
    create_stance(cfg, args.title, author)
  elif args.command == "signal":
    create_signal(cfg, args.title, args.type, author)
  elif args.command == "framework":
    create_framework(cfg, args.title, args.source, author)
  elif args.command == "draft":
    create_draft(cfg, args.title, author)
  elif args.command == "journey":
    create_journey(cfg, args.title, author)


if __name__ == "__main__":
  main()
