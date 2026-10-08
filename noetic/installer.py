"""Install or update the Taste Engine into an Obsidian (or any markdown) vault.

  noetic install --vault "/path/to/vault" --owner "Ada"   (or: uvx noetic-cli install ...)
  python install.py --vault "/path/to/vault" --owner "Ada"

Running it again updates the engine-owned files (canonical commands/agents, the noetic package,
workflows) and never touches your notes. Seed files (interests.md,
Twitter/README.md, posted.md) are created only if they're missing.

Agent adapters (CLAUDE.md, AGENTS.md, GEMINI.md, .claude/, .gemini/, .agent/) are GENERATED from the
canonical sources by `noetic.adapters.sync`. Pick them with --agents (default: all); the choice
is recorded in the vault config under "adapters". --with-wiki copies the generic Noetic wiki template
(never overwriting existing files).
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

PKG = Path(__file__).resolve().parent  # .../noetic
SEED = PKG / "seed"
AGENTS_SRC = PKG / "agents"


def _workflows_dir() -> Path:
  from noetic.orchestration.loader import workflows_dir
  d = workflows_dir()
  if d is None:
    raise SystemExit("workflows package not found; reinstall noetic-cli")
  return d


PROJECTS_DIR = _workflows_dir()
CONFIG_NAME = "taste-engine.config.json"
WIKI_SEED = SEED / "overmind-wiki"
DEFAULT_OVERMIND_DIR = "OverMind"

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
  "canonical/commands",
  "canonical/agents",
  "playbooks",
  "scripts",
]


def build_config(args: argparse.Namespace, vault: Path) -> dict:
  path = vault / CONFIG_NAME
  cfg = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
  cfg.setdefault("paths", {})
  # Explicit flags override; otherwise keep what's there; otherwise defaults.
  cfg["owner"] = args.owner or cfg.get("owner") or "Owner"
  cfg["agent"] = args.agent or cfg.get("agent") or "Claude Code"
  cfg["x_char_limit"] = args.x_char_limit or cfg.get("x_char_limit") or 280
  from noetic.adapters.sync import resolve_agents  # noqa: E402 (path set above)
  # The vault config is the single place that records which agent adapters are generated.
  cfg["adapters"] = resolve_agents([a for a in args.agents.split(",") if a] if args.agents else None, cfg)
  for key, flag, default in [
    ("engine", args.engine_dir, "taste-engine"),
    ("frameworks", args.frameworks_dir, "frameworks"),
    ("twitter", args.twitter_dir, "Twitter"),
    ("overmind", args.overmind_dir, DEFAULT_OVERMIND_DIR if getattr(args, "with_wiki", False) else None),
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
    if src.name == "__init__.py":  # package markers stay with the package copy
      continue
    dst = dst_dir / src.name
    if rendered:
      dst.write_text(render(src.read_text(encoding="utf-8"), cfg), encoding="utf-8")
    else:
      shutil.copyfile(src, dst)
    written.append(str(dst))
  return written


OBSOLETE_SCRIPTS = ["te_config.py", "agents.py", "render.py", "schema_check.py"]


def copy_package(src: Path, dst: Path, keep: set[str] | None = None) -> list[str]:
  """Replace the installed package wholesale so removed modules don't linger.

  `keep`: when given, only these top-level subfolders are copied (plus the package's own files).
  """
  if dst.exists():
    shutil.rmtree(dst)
  skip = shutil.ignore_patterns("__pycache__", "*.pyc")

  def ignore(d: str, names: list[str]) -> set[str]:
    out = set(skip(d, names))
    if keep is not None and Path(d) == src:
      out |= {n for n in names if (src / n).is_dir() and n not in keep}
    return out

  shutil.copytree(src, dst, ignore=ignore)
  return [str(p) for p in dst.rglob("*.py")]


def seed(src: Path, dst: Path, cfg: dict) -> str | None:
  if dst.exists() or not src.exists():  # project seeds (e.g. seed/twitter) are optional
    return None
  dst.parent.mkdir(parents=True, exist_ok=True)
  dst.write_text(render(src.read_text(encoding="utf-8"), cfg), encoding="utf-8")
  return str(dst)


def install_canonical(vault: Path, cfg: dict, project_names: list[str]) -> list[str]:
  """Copy the provider-neutral sources into the vault; adapters are generated from this copy."""
  dst = vault / cfg["paths"]["engine"] / "canonical"
  if dst.exists():
    shutil.rmtree(dst)
  written = []
  for pname in project_names:
    if (PROJECTS_DIR / pname / "commands").is_dir():
      written += copy_owned(PROJECTS_DIR / pname / "commands", dst / "commands", cfg, "*.md", rendered=False)
  written += copy_owned(AGENTS_SRC, dst / "agents", cfg, "*.md", rendered=False)
  shutil.copyfile(SEED / "AGENTS.block.md", dst / "AGENTS.block.md")
  return written + [str(dst / "AGENTS.block.md")]


def install_wiki(vault: Path, cfg: dict) -> list[str]:
  """Copy the generic wiki template. Existing files are never overwritten."""
  base = vault / cfg["paths"]["overmind"]
  created = []
  for src in sorted(WIKI_SEED.rglob("*")):
    if src.is_file():
      s = seed(src, base / src.relative_to(WIKI_SEED), cfg)
      if s:
        created.append(s)
  return created


def install_project(project_name: str, vault: Path, cfg: dict) -> list[str]:
  """Seed the vault-side folders of a workflow pack (e.g. workflows/twitter).

  The pack's code, prompts, schemas and templates ship inside the installed `workflows` package;
  commands are canonical (install_canonical) and reach each agent through the adapters.
  """
  proj_dir = PROJECTS_DIR / project_name
  if not proj_dir.is_dir():
    return []
  written = []
  target_folder = cfg["paths"].get(project_name)
  if target_folder:
    target_dir = vault / target_folder
    for d in ("journey", "drafts", "ready"):
      (target_dir / d).mkdir(parents=True, exist_ok=True)
    if (proj_dir / "seed").is_dir():
      for s in (proj_dir / "seed").glob("*.md"):
        r = seed(s, target_dir / s.name, cfg)
        if r:
          written.append(r)
  return written


def main(argv: list[str] | None = None):
  p = argparse.ArgumentParser(description="Install/update the Taste Engine into a vault")
  p.add_argument("--vault", required=True, help="Path to your vault root")
  p.add_argument("--owner", help="Your name (used in attribution)")
  p.add_argument("--agent", help="Agent label for AI-authored notes (default: Claude Code)")
  p.add_argument("--engine-dir", help="Engine folder inside the vault (default: taste-engine)")
  p.add_argument("--frameworks-dir", help="Frameworks folder (default: frameworks)")
  p.add_argument("--twitter-dir", help="Build-in-public folder (default: Twitter)")
  p.add_argument("--overmind-dir", help="Optional Overmind folder (goals/quests/log integration)")
  p.add_argument("--x-char-limit", type=int, help="Per-tweet limit (default 280; raise for X Premium)")
  p.add_argument("--agents", help="Comma list of agent adapters to generate: claude,codex,gemini,antigravity,universal (default: all four main ones, or what the vault config already records)")
  p.add_argument("--with-wiki", action="store_true", help="Copy the generic Noetic wiki template (never overwrites existing files)")
  p.add_argument("--projects", nargs="*", help="Project packs to install (default: all packs in workflows/)")
  args = p.parse_args(argv)

  vault = Path(args.vault).expanduser().resolve()
  if not vault.is_dir():
    sys.exit(f"Vault not found: {vault}")

  try:
    cfg = build_config(args, vault)
  except ValueError as e:
    sys.exit(str(e))
  engine = vault / cfg["paths"]["engine"]
  frameworks = vault / cfg["paths"]["frameworks"]

  for d in ENGINE_DIRS:
    (engine / d).mkdir(parents=True, exist_ok=True)
  (frameworks / "briefs").mkdir(parents=True, exist_ok=True)

  (vault / CONFIG_NAME).write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

  written = []
  proj_names = args.projects if args.projects is not None else [p.name for p in sorted(PROJECTS_DIR.iterdir()) if p.is_dir() and not p.name.startswith(("__", "."))]
  # 1. Install the core package and the selected workflows as importable packages.
  scripts = engine / "scripts"
  scripts.mkdir(parents=True, exist_ok=True)
  for old in OBSOLETE_SCRIPTS:  # modules that moved into the noetic package
    (scripts / old).unlink(missing_ok=True)
  written += copy_package(PKG, scripts / "noetic")
  written += copy_package(PROJECTS_DIR, scripts / "workflows", keep=set(proj_names))

  # 2. Canonical commands/agents and per-workflow vault folders
  written += install_canonical(vault, cfg, proj_names)
  for pname in proj_names:
    written += install_project(pname, vault, cfg)

  seeded = [s for s in (
    seed(SEED / "interests.md", engine / "interests.md", cfg),
  ) if s]

  wiki = install_wiki(vault, cfg) if args.with_wiki else []

  from noetic.adapters.sync import sync
  report = sync(vault, cfg["adapters"])

  print(f"Taste Engine installed into {vault}")
  print(f"  config:     {CONFIG_NAME}")
  print(f"  adapters:   {', '.join(report.agents)} ({report.summary()})")
  for n in report.notes:
    print(f"    note: {n}")
  print(f"  updated {len(written)} engine files (canonical commands/agents, noetic package, workflows)")
  if args.with_wiki:
    print(f"  wiki:       {len(wiki)} template files created under {cfg['paths']['overmind']}/ (existing files kept)")
  for s in seeded:
    print(f"  seeded:     {s}")
  print("\nNext: edit interests.md, then open the vault in Claude Code and try `/ingest <a book you love>`.")


if __name__ == "__main__":
  main()
