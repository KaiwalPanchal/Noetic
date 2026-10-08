"""Daily Librarian: deterministic inbox triage (no LLM, never deletes or edits your notes).

For every note in `inbox/` it reports: empty/duplicate files, existing vault notes it likely relates to
(by shared title words and exact title mentions), and its headings. The digest lands as a `pending_review`
note. State in .taste-engine/librarian.json keeps it to once per 24 hours unless forced.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re

from overmind.knowledge.config import Config
from overmind.knowledge.context import iter_notes

INTERVAL = timedelta(hours=24)
STOP = {"the", "and", "for", "with", "from", "that", "this", "note", "notes", "untitled", "new", "into", "how", "what"}


def _words(text: str) -> set[str]:
  return {w for w in re.findall(r"[a-z0-9]{4,}", text.lower()) if w not in STOP}


def inbox_dir(cfg: Config) -> Path:
  return cfg.vault / "inbox"


def due(cfg: Config, now: datetime | None = None) -> bool:
  state = cfg.state_dir / "librarian.json"
  if not state.exists():
    return True
  try:
    last = datetime.fromisoformat(json.loads(state.read_text(encoding="utf-8"))["last_run"])
  except (KeyError, ValueError, json.JSONDecodeError):
    return True
  return (now or datetime.now()) - last >= INTERVAL


def scan(cfg: Config) -> dict:
  inbox = inbox_dir(cfg)
  items, seen = [], {}
  vault_notes = [(p.stem, _words(p.stem)) for p in iter_notes(cfg) if inbox not in p.parents]
  for f in sorted(inbox.glob("*.md")) if inbox.is_dir() else []:
    text = f.read_text(encoding="utf-8", errors="replace")
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S).strip()
    digest = hashlib.sha1(body.encode("utf-8")).hexdigest()
    flags = []
    if not body:
      flags.append("empty")
    elif digest in seen:
      flags.append(f"duplicate of {seen[digest]}")
    seen.setdefault(digest, f.name)
    mine = _words(f.stem) | _words(body[:2000])
    scored = set()
    for stem, words in vault_notes:
      if len(stem) > 4 and stem.lower() in body.lower():
        scored.add((2 + len(words & mine), stem))
      elif words and len(words & mine) >= max(2, len(words) // 2 + 1):
        scored.add((len(words & mine), stem))
    related = [s for _, s in sorted(scored, reverse=True)[:5]]
    headings = [l.lstrip("# ").strip() for l in body.splitlines() if l.startswith("#")][:5]
    items.append({"file": f.name, "flags": flags, "related": related, "headings": headings, "chars": len(body)})
  return {"generated": datetime.now().isoformat(timespec="seconds"), "inbox": str(inbox), "items": items}


def render(report: dict) -> str:
  lines = [f"# Librarian digest — {report['generated'][:10]}", "",
           f"{len(report['items'])} item(s) in inbox. Nothing was moved, edited or deleted.", ""]
  for it in report["items"]:
    flags = f"  **[{', '.join(it['flags'])}]**" if it["flags"] else ""
    lines.append(f"## {it['file']}{flags}")
    lines.append("Related: " + (", ".join(f"[[{r}]]" for r in it["related"]) if it["related"] else "none found"))
    if it["headings"]:
      lines.append("Headings: " + "; ".join(it["headings"]))
    lines.append("")
  return "\n".join(lines).rstrip() + "\n"


def run_librarian(cfg: Config, force: bool = False) -> Path | None:
  """Write the digest if due (or forced). Returns the note path, or None when skipped."""
  if not force and not due(cfg):
    return None
  report = scan(cfg)
  out_dir = (cfg.overmind / "wiki" / "librarian") if cfg.overmind else (cfg.engine / "librarian")
  out_dir.mkdir(parents=True, exist_ok=True)
  path = out_dir / f"digest-{datetime.now():%Y-%m-%d}.md"
  path.write_text("---\nauthor: ai-agent\nstatus: pending_review\nkind: librarian-digest\n---\n" + render(report),
                  encoding="utf-8")
  cfg.state_dir.mkdir(parents=True, exist_ok=True)
  (cfg.state_dir / "librarian.json").write_text(json.dumps({"last_run": report["generated"]}), encoding="utf-8")
  return path


def schedule_hint(vault: Path) -> dict[str, str]:
  """Scheduler commands to paste. We print them; we never install a scheduled task for you."""
  return {
      "windows": f'schtasks /Create /SC DAILY /ST 08:00 /TN OverMindLibrarian /TR "overmind librarian --vault \\"{vault}\\""',
      "cron": f'0 8 * * * overmind librarian --vault "{vault}"',
  }
