"""Knowledge layer: build the context a model sees (12-factor #3).

Python decides what goes into every prompt. Everything is budgeted by
character count, and private folders (config `private_paths`) are never read.
"""

from __future__ import annotations

from pathlib import Path
import re

from taste_engine.knowledge.config import Config

# Context budgets in characters.
BUDGET = {"interests": 3000, "taste": 4500, "note": 12000, "vault_notes": 9000, "voice": 3000, "framework": 5000}
SKIP_DIRS = {".obsidian", ".trash", ".taste-engine", ".claude", ".git", ".stfolder", "node_modules"}


def read_body(path: Path, limit: int) -> str:
  text = path.read_text(encoding="utf-8", errors="replace")
  if text.startswith("---"):
    end = text.find("\n---", 3)
    if end != -1:
      text = text[end + 4:]
  text = re.sub(r"^> \[!NOTE\].*$", "", text, flags=re.M).strip()
  return text if len(text) <= limit else text[:limit] + "\n…[truncated]"


def is_private(cfg: Config, path: Path) -> bool:
  rel = path.relative_to(cfg.vault).as_posix().lower()
  return any(rel.startswith(p.strip("/").lower() + "/") or rel == p.strip("/").lower() for p in cfg.private_paths)


def iter_notes(cfg: Config, *, skip_roots: tuple[Path, ...] = ()):
  """Every readable, non-private markdown note in the vault."""
  for f in cfg.vault.rglob("*.md"):
    if any(part in SKIP_DIRS for part in f.relative_to(cfg.vault).parts):
      continue
    if is_private(cfg, f) or any(root in f.parents for root in skip_roots):
      continue
    yield f


def resolve_vault_path(cfg: Config, raw: str) -> Path | None:
  for candidate in (Path(raw), cfg.vault / raw, cfg.vault / f"{raw}.md"):
    if candidate.is_file():
      return candidate.resolve()
  hits = [p for p in cfg.vault.rglob(f"*{raw}*.md") if not any(s in p.parts for s in SKIP_DIRS)]
  return hits[0].resolve() if len(hits) == 1 else None


def interests(cfg: Config) -> str:
  f = cfg.engine / "interests.md"
  return read_body(f, BUDGET["interests"]) if f.exists() else "(no interests.md yet)"


def interest_names(cfg: Config) -> list[str]:
  f = cfg.engine / "interests.md"
  return re.findall(r"^## (.+)$", f.read_text(encoding="utf-8"), re.M) if f.exists() else []


def taste(cfg: Config) -> str:
  parts, used = [], 0
  for sub in ("negative-filters", "stances"):
    for f in sorted((cfg.engine / "01-taste-graph" / sub).glob("*.md")):
      chunk = f"### {sub[:-1]}: {f.stem}\n{read_body(f, 600)}"
      if used + len(chunk) > BUDGET["taste"]:
        break
      parts.append(chunk)
      used += len(chunk)
  return "\n\n".join(parts) or "(no stances or filters yet)"


def frameworks(cfg: Config) -> str:
  rows = []
  for f in sorted(cfg.frameworks.glob("*.md")):
    m = re.search(r"## Core Idea\s+(.+)", f.read_text(encoding="utf-8", errors="replace"))
    rows.append(f"- {f.stem}: {m.group(1).strip()[:160] if m else ''}")
  return "\n".join(rows) or "(none yet)"


def search(cfg: Config, terms: list[str], limit: int = 12) -> str:
  """Keyword search over the vault, skipping private and engine-output folders.

  Swap point: a semantic index from a future knowledge pipeline can replace this
  without changing any caller.
  """
  terms = [t.lower() for t in terms if len(t) > 3]
  if not terms:
    return "(no search terms)"
  scored = []
  for f in iter_notes(cfg, skip_roots=(cfg.twitter, cfg.engine / "03-pipeline", cfg.state_dir)):
    try:
      text = f.read_text(encoding="utf-8", errors="replace")
    except OSError:
      continue
    low = text.lower()
    score = sum(low.count(t) for t in terms) + 5 * sum(t in f.stem.lower() for t in terms)
    if score:
      scored.append((score, f, text))
  scored.sort(key=lambda x: -x[0])
  out, used = [], 0
  for _, f, text in scored[:limit]:
    low = text.lower()
    hit = min((low.find(t) for t in terms if t in low), default=0)
    excerpt = text[max(0, hit - 200): hit + 500].strip().replace("\n", " ")
    chunk = f"### {f.relative_to(cfg.vault).as_posix()}\n{excerpt}"
    if used + len(chunk) > BUDGET["vault_notes"]:
      break
    out.append(chunk)
    used += len(chunk)
  return "\n\n".join(out) or "(nothing relevant found in the vault)"


def archive(cfg: Config) -> str:
  titles = [f.stem for f in (cfg.engine / "03-pipeline" / "04-archive").glob("*.md") if f.stem != "README"]
  posted = cfg.twitter / "posted.md"
  if posted.exists():
    titles += re.findall(r"\|\s*\[([^\]]+)\]", posted.read_text(encoding="utf-8"))
  return "\n".join(f"- {t}" for t in titles) or "(nothing published yet)"


def voice(cfg: Config) -> str:
  files = sorted(
    list((cfg.engine / "03-pipeline" / "04-archive").glob("*.md")) + list((cfg.engine / "03-pipeline" / "02-drafts").glob("*.md")),
    key=lambda p: p.stat().st_mtime, reverse=True,
  )
  files = [f for f in files if f.stem != "README"][:2]
  return "\n\n".join(f"### {f.stem}\n{read_body(f, BUDGET['voice'] // 2)}" for f in files) or "(no examples yet)"


def playbooks(cfg: Config) -> str:
  out = []
  for name in ("twitter-hook-frameworks", "thread-templates"):
    f = cfg.engine / "playbooks" / f"{name}.md"
    if f.exists():
      out.append(f"### {name}\n{read_body(f, 1500)}")
  return "\n\n".join(out) or "(none)"


def recent_log(cfg: Config, limit: int = 3000) -> str:
  if not cfg.overmind:
    return ""
  logs = sorted((cfg.overmind / "wiki" / "log").glob("*.md"))
  return read_body(logs[-1], limit)[-limit:] if logs else ""
