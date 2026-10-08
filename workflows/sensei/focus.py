"""Sensei focus defense and tangent parking.

Tracks the single active commitment in <overmind>/wiki/focus.md, logs changes
to <overmind>/wiki/log/YYYY-MM.md, and parks tangents in ideas/PARKED.md.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import re
from typing import Any

from noetic.knowledge.config import Config
from noetic.knowledge.registry import split_frontmatter
from noetic.orchestration.run import PipelineError
from noetic.tools.registry import tool

BODY = """# Current Focus

One commitment at a time. This file is what the Sensei defends. It is written by `noetic focus`; don't hand-edit.

## Parked tangents
Anything that comes up mid-focus and isn't this goes to `ideas/PARKED.md`. Nothing is lost, nothing is started.

## Changing focus
`noetic focus "<new commitment>"`. A switch is allowed. A silent drift is the thing being prevented.
"""


def _require_overmind(cfg: Config) -> Path:
  wiki = cfg.wiki or cfg.overmind
  if wiki is None:
    raise PipelineError("NO_OVERMIND", "paths.wiki (or paths.overmind) is not set in noetic.config.json")
  return wiki

_require_wiki = _require_overmind


def _q(value: str) -> str:
  return '"' + str(value).replace('"', "'").replace("\n", " ").strip() + '"'


def get_focus(cfg: Config) -> dict[str, Any]:
  """Current commitment from wiki/focus.md, or {} if none is set."""
  overmind = _require_overmind(cfg)
  focus_file = overmind / "wiki" / "focus.md"
  if not focus_file.exists():
    return {}
  fm, _ = split_frontmatter(focus_file.read_text(encoding="utf-8"))
  return fm if fm.get("commitment") else {}


def write_focus(cfg: Config, commitment: str, project: str = "", done_when: str = "") -> None:
  """Write the current focus to wiki/focus.md."""
  overmind = _require_overmind(cfg)
  focus_file = overmind / "wiki" / "focus.md"
  focus_file.parent.mkdir(parents=True, exist_ok=True)
  focus_file.write_text(
    "---\n"
    f"project: {_q(project)}\n"
    f"commitment: {_q(commitment)}\n"
    f"done_when: {_q(done_when)}\n"
    f'committed: "{date.today().isoformat()}"\n'
    "---\n" + BODY,
    encoding="utf-8",
  )


def clear_focus(cfg: Config) -> None:
  """Leave a valid focus file with no commitment."""
  overmind = _require_overmind(cfg)
  focus_file = overmind / "wiki" / "focus.md"
  focus_file.parent.mkdir(parents=True, exist_ok=True)
  focus_file.write_text('---\ncommitment: ""\n---\n' + BODY, encoding="utf-8")


def days_on(focus: dict) -> int | None:
  """Days spent on this focus so far."""
  try:
    return (date.today() - date.fromisoformat(focus.get("committed", ""))).days + 1
  except (ValueError, TypeError):
    return None


def log_event(cfg: Config, kind: str, text: str) -> None:
  """Append '## DATE — <kind>' to this month's log in wiki/log/YYYY-MM.md."""
  overmind = _require_overmind(cfg)
  log_dir = overmind / "wiki" / "log"
  log_dir.mkdir(parents=True, exist_ok=True)
  path = log_dir / f"{date.today():%Y-%m}.md"
  if not path.exists():
    path.write_text(f"# Log — {date.today():%B %Y}\n", encoding="utf-8")
  with path.open("a", encoding="utf-8") as fh:
    fh.write(f"\n## {date.today().isoformat()} — {kind}\n{text.rstrip()}\n")


def recent_switches(cfg: Config, days: int = 7) -> int:
  """Count 'Focus switched' log entries in the last `days` days (this and last month's logs)."""
  wiki = cfg.wiki or cfg.overmind
  if wiki is None:
    return 0
  log_dir = wiki / "wiki" / "log"
  today = date.today()
  first_of_month = today.replace(day=1)
  prev = (first_of_month - timedelta(days=1)).replace(day=1)
  count = 0
  for month in (prev, first_of_month):
    path = log_dir / f"{month:%Y-%m}.md"
    try:
      text = path.read_text(encoding="utf-8")
    except OSError:
      continue
    for m in re.finditer(r"^## (\d{4}-\d{2}-\d{2}) — Focus switched", text, flags=re.M):
      try:
        if (today - date.fromisoformat(m.group(1))).days < days:
          count += 1
      except ValueError:
        pass
  return count


def switch_focus(cfg: Config, commitment: str, project: str = "", done_when: str = "") -> dict:
  """Make `commitment` the focus and log it. Returns the previous focus ({} if none)."""
  prev = get_focus(cfg)
  write_focus(cfg, commitment, project, done_when)
  lines = [f"- to: {commitment}", f"- project: {project}", f"- done when: {done_when}"]
  if prev:
    n = days_on(prev)
    lines.insert(0, f"- from: {prev['commitment']}" + (f" (day {n}, unfinished)" if n else " (unfinished)"))
  log_event(cfg, "Focus switched" if prev else "Focus set", "\n".join(lines))
  return prev


def finish_focus(cfg: Config) -> dict:
  """Mark current focus done, log it, clear it. Returns the finished focus ({} if none)."""
  prev = get_focus(cfg)
  if not prev:
    return {}
  n = days_on(prev)
  log_event(cfg, "Focus done", f"- {prev['commitment']} ({prev.get('project', '?')})" + (f", took {n} day(s)" if n else ""))
  clear_focus(cfg)
  return prev


def park_idea(cfg: Config, title: str, note: str, thought: str = "", focus: dict | None = None) -> Path:
  """Append a tangent to ideas/PARKED.md. Never overwrites."""
  path = cfg.vault / "ideas" / "PARKED.md"
  path.parent.mkdir(parents=True, exist_ok=True)
  if not path.exists():
    path.write_text(
      "# Parked tangents\n\nCaptured by Sensei while a focus was active.\n",
      encoding="utf-8",
    )
  focus_label = (focus or {}).get("commitment", "?") if focus else "?"
  entry = (
    f"\n## {title}\n"
    f"- parked: {date.today().isoformat()} · while focused on: {focus_label}\n"
    f"- {note}\n"
  )
  if thought:
    entry += f"- original thought: {thought.strip()}\n"
  with path.open("a", encoding="utf-8") as fh:
    fh.write(entry)
  return path


@tool("focus_get", help="get the current focus commitment or {}", needs_cfg=True)
def tool_focus_get(cfg: Config) -> dict:
  return get_focus(cfg)


@tool("park_idea", help="park an idea to ideas/PARKED.md", needs_cfg=True)
def tool_park_idea(cfg: Config, title: str, note: str, thought: str = "", focus: dict | None = None) -> str:
  p = park_idea(cfg, title, note, thought=thought, focus=focus)
  return str(p)
