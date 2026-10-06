"""Install or update the Taste Engine into an Obsidian (or any markdown) vault.

  python install.py --vault "/path/to/vault" --owner "Ada"

Running it again updates the engine-owned files (commands, scripts, package, templates, prompts, schemas)
and never touches your notes. Seed files (interests.md, Twitter/README.md,
posted.md) are created only if they're missing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
  sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent
CONFIG_NAME = "taste-engine.config.json"
BLOCK_RE = re.compile(r"<!-- taste-engine:start -->.*?<!-- taste-engine:end -->\n?", re.S)

ENGINE_DIRS = [
  "01-taste-graph/stances",
  "01-taste-graph/negative-filters",
  "01-taste-graph/exemplars",
  "02-signals/papers",
  "02-signals/repos",
  "02-signals/postmortems",
  "02-signals/web",
  "03-pipeline/00-inbox",
  "03-pipeline/01-curation",
  "03-pipeline/02-drafts",
  "03-pipeline/03-ready-to-post",
  "03-pipeline/04-archive",
  "playbooks",
  "scripts",
  "templates",
  "prompts",
  "schemas",
]


def build_config(args: argparse.Namespace, vault: Path) -> dict:
  path = vault / CONFIG_NAME
  cfg = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
  cfg.setdefault("paths", {})
  # Explicit flags override; otherwise keep what's there; otherwise defaults.
  cfg["owner"] = args.owner or cfg.get("owner") or "Owner"
  cfg["agent"] = args.agent or cfg.get("agent") or "Claude Code"
  cfg["x_char_limit"] = args.x_char_limit or cfg.get("x_char_limit") or 280
  for key, flag, default in [
    ("engine", args.engine_dir, "taste-engine"),
    ("frameworks", args.frameworks_dir, "frameworks"),
    ("twitter", args.twitter_dir, "Twitter"),
    ("overmind", args.overmind_dir, None),
  ]:
    cfg["paths"][key] = flag or cfg["paths"].get(key) or default
  return cfg


def render(text: str, cfg: dict) -> str:
  values = {
    "owner": cfg["owner"],
    "owner_slug": re.sub(r"[^\w-]+", "-", cfg["owner"].lower()).strip("-"),
    "agent": cfg["agent"],
    **{k: v or "" for k, v in cfg["paths"].items()},
  }
  return re.sub(r"\{\{(\w+)\}\}", lambda m: str(values.get(m.group(1), m.group(0))), text)


def copy_owned(src_dir: Path, dst_dir: Path, cfg: dict, pattern: str, rendered: bool) -> list[str]:
  dst_dir.mkdir(parents=True, exist_ok=True)
  written = []
  for src in sorted(src_dir.glob(pattern)):
    dst = dst_dir / src.name
    if rendered:
      dst.write_text(render(src.read_text(encoding="utf-8"), cfg), encoding="utf-8")
    else:
      shutil.copyfile(src, dst)
    written.append(str(dst))
  return written


OBSOLETE_SCRIPTS = ["te_config.py", "agents.py", "render.py", "schema_check.py"]


def copy_package(src: Path, dst: Path) -> list[str]:
  """Replace the installed package wholesale so removed modules don't linger."""
  if dst.exists():
    shutil.rmtree(dst)
  shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
  return [str(p) for p in dst.rglob("*.py")]


def seed(src: Path, dst: Path, cfg: dict) -> str | None:
  if dst.exists():
    return None
  dst.parent.mkdir(parents=True, exist_ok=True)
  dst.write_text(render(src.read_text(encoding="utf-8"), cfg), encoding="utf-8")
  return str(dst)


def update_claude_md(vault: Path, cfg: dict) -> str:
  block = render((REPO / "seed" / "CLAUDE.block.md").read_text(encoding="utf-8"), cfg)
  path = vault / "CLAUDE.md"
  if not path.exists():
    path.write_text(f"# Vault instructions\n\n{block}", encoding="utf-8")
    return "created"
  text = path.read_text(encoding="utf-8")
  if BLOCK_RE.search(text):
    path.write_text(BLOCK_RE.sub(lambda _: block, text), encoding="utf-8")
    return "updated block"
  path.write_text(text.rstrip() + "\n\n" + block, encoding="utf-8")
  return "appended block"


def main():
  p = argparse.ArgumentParser(description="Install/update the Taste Engine into a vault")
  p.add_argument("--vault", required=True, help="Path to your vault root")
  p.add_argument("--owner", help="Your name (used in attribution)")
  p.add_argument("--agent", help="Agent label for AI-authored notes (default: Claude Code)")
  p.add_argument("--engine-dir", help="Engine folder inside the vault (default: taste-engine)")
  p.add_argument("--frameworks-dir", help="Frameworks folder (default: frameworks)")
  p.add_argument("--twitter-dir", help="Build-in-public folder (default: Twitter)")
  p.add_argument("--overmind-dir", help="Optional Overmind folder (goals/quests/log integration)")
  p.add_argument("--x-char-limit", type=int, help="Per-tweet limit (default 280; raise for X Premium)")
  args = p.parse_args()

  vault = Path(args.vault).expanduser().resolve()
  if not vault.is_dir():
    sys.exit(f"Vault not found: {vault}")

  cfg = build_config(args, vault)
  engine = vault / cfg["paths"]["engine"]
  frameworks = vault / cfg["paths"]["frameworks"]
  twitter = vault / cfg["paths"]["twitter"]

  for d in ENGINE_DIRS:
    (engine / d).mkdir(parents=True, exist_ok=True)
  (frameworks / "briefs").mkdir(parents=True, exist_ok=True)
  for d in ("journey", "drafts", "ready"):
    (twitter / d).mkdir(parents=True, exist_ok=True)

  (vault / CONFIG_NAME).write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

  written = []
  written += copy_owned(REPO / "engine" / "commands", vault / ".claude" / "commands", cfg, "*.md", rendered=False)
  written += copy_owned(REPO / "engine" / "scripts", engine / "scripts", cfg, "*.py", rendered=False)
  written += copy_package(REPO / "engine" / "scripts" / "taste_engine", engine / "scripts" / "taste_engine")
  for old in OBSOLETE_SCRIPTS:  # modules that moved into the taste_engine package
    (engine / "scripts" / old).unlink(missing_ok=True)
  written += copy_owned(REPO / "engine" / "templates", engine / "templates", cfg, "*.md", rendered=True)
  # Prompts keep their {{placeholders}}: the pipeline fills them at run time.
  written += copy_owned(REPO / "engine" / "prompts", engine / "prompts", cfg, "*.md", rendered=False)
  written += copy_owned(REPO / "engine" / "schemas", engine / "schemas", cfg, "*.json", rendered=False)

  seeded = [s for s in (
    seed(REPO / "seed" / "interests.md", engine / "interests.md", cfg),
    seed(REPO / "seed" / "twitter" / "README.md", twitter / "README.md", cfg),
    seed(REPO / "seed" / "twitter" / "posted.md", twitter / "posted.md", cfg),
  ) if s]

  claude_md = update_claude_md(vault, cfg)

  print(f"Taste Engine installed into {vault}")
  print(f"  config:     {CONFIG_NAME}")
  print(f"  CLAUDE.md:  {claude_md}")
  print(f"  updated {len(written)} engine files (commands, scripts, package, templates, prompts, schemas)")
  for s in seeded:
    print(f"  seeded:     {s}")
  print("\nNext: edit interests.md, then open the vault in Claude Code and try `/ingest <a book you love>`.")


if __name__ == "__main__":
  main()
