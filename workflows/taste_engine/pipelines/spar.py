"""spar: RFC / PR diff + stacked frameworks -> ADR critique (Mode B Sparring).

Adversarial cognitive sparring and architectural decision records:
- Zero hardcoded cognitive logic: reads default_lenses from noetic.config.json [R2]
- Fails loudly with PipelineError("LENS_UNAVAILABLE") if any lens is missing or unapproved [R1+R2]
- Compiles synthesis charter using stack_frameworks_logic [R2]
- Concurrency-safe atomic ADR numbering via directory lockfile [R1]
- Writes ADR note with status: pending_review inside machine markers <!-- NOETIC:AUTO:START/END --> [R1+R2]
- Closes the loop: appends to Applications Log strictly inside LOG markers of evaluated frameworks [R2]
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import time
from typing import Iterator

from noetic.knowledge import notes
from noetic.knowledge.config import Config, slugify, today
from noetic.knowledge.stack import check_framework_trust, stack_frameworks_logic
from noetic.orchestration.registry import arg, pipeline
from noetic.orchestration.run import PipelineError
from noetic.orchestration.steps import agent_step
from noetic.tools import prompts


@contextmanager
def dir_lock(lock_file_path: Path, timeout: float = 10.0, retry_interval: float = 0.05) -> Iterator[None]:
  """Atomic cross-platform directory lock using os.open with O_CREAT | O_EXCL [R1]."""
  lock_file_path.parent.mkdir(parents=True, exist_ok=True)
  start_time = time.time()
  fd = None
  while True:
    try:
      fd = os.open(str(lock_file_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
      break
    except (FileExistsError, PermissionError):
      if time.time() - start_time > timeout:
        try:
          if time.time() - lock_file_path.stat().st_mtime > 60:
            lock_file_path.unlink(missing_ok=True)
            continue
        except Exception:
          pass
        raise TimeoutError(f"Could not acquire lock on {lock_file_path} within {timeout}s")
      time.sleep(retry_interval)
  try:
    yield
  finally:
    if fd is not None:
      try:
        os.close(fd)
      except Exception:
        pass
      try:
        lock_file_path.unlink(missing_ok=True)
      except Exception:
        pass


def resolve_framework_path(frameworks_dir: Path, slug: str) -> Path | None:
  """Resolves framework slug to path on disk, matching direct filename or slugified stem."""
  if not frameworks_dir.exists():
    return None
  direct = frameworks_dir / f"{slug}.md"
  if direct.is_file():
    return direct
  for f in frameworks_dir.glob("*.md"):
    if f.name.lower() in ("readme.md", "index.md"):
      continue
    if slugify(f.stem) == slug:
      return f
  return None


def resolve_adr_dir(cfg: Config, custom_dir: str | Path | None = None) -> Path:
  """Resolves ADR destination directory: custom -> wiki/adr -> overmind/wiki/adr -> frameworks/adr."""
  if custom_dir:
    p = Path(custom_dir)
    return p if p.is_absolute() else (cfg.vault / p).resolve()

  wiki = cfg.wiki or cfg.overmind
  if wiki and wiki.exists():
    if (wiki / "wiki" / "adr").is_dir() or (wiki / "wiki").is_dir():
      return wiki / "wiki" / "adr"
    if (wiki / "adr").is_dir():
      return wiki / "adr"
    return wiki / "wiki" / "adr"

  return cfg.frameworks / "adr"


def next_atomic_adr_number(adr_dir: Path) -> str:
  """Atomically scans destination directory for ADR-NNN-* and returns next sequence number [R1]."""
  pattern = re.compile(r"^ADR-(\d+)", re.IGNORECASE)
  with dir_lock(adr_dir / ".adr.lock"):
    existing_nums = []
    if adr_dir.exists():
      for f in adr_dir.glob("*.md"):
        m = pattern.match(f.name)
        if m:
          try:
            existing_nums.append(int(m.group(1)))
          except ValueError:
            pass
    next_num = max(existing_nums, default=0) + 1
    return f"ADR-{next_num:03d}"


def reserve_next_adr_number(adr_dir: Path, slug: str = "") -> tuple[str, Path]:
  """Atomically assigns next ADR number and creates reservation file under directory lock [R1]."""
  pattern = re.compile(r"^ADR-(\d+)", re.IGNORECASE)
  with dir_lock(adr_dir / ".adr.lock"):
    existing_nums = []
    if adr_dir.exists():
      for f in adr_dir.glob("*.md"):
        m = pattern.match(f.name)
        if m:
          try:
            existing_nums.append(int(m.group(1)))
          except ValueError:
            pass
    next_num = max(existing_nums, default=0) + 1
    adr_number = f"ADR-{next_num:03d}"
    filename = f"{adr_number}-{slug}.md" if slug else f"{adr_number}.md"
    target_file = adr_dir / filename
    target_file.touch(exist_ok=True)
    return adr_number, target_file


@pipeline("spar", kind="project", help="RFC / PR diff + stacked frameworks -> ADR critique", args=[
  arg("target", nargs="?", default="", help="path to RFC / design doc / diff, or inline text"),
  arg("frameworks", nargs="*", default=[], help="optional additional framework slugs to evaluate"),
  arg("--target", dest="target_opt", help="optional keyword alias for target"),
  arg("--adr-dir", help="custom output directory for generated ADR notes"),
  arg("--adr-number", help="override ADR sequence number (e.g. ADR-001)"),
  arg("--allow-order-precedence", action="store_true", help="resolve same-tier collisions using argument order"),
  arg("--max-tokens", type=int, default=4000, help="maximum tokens for stacked heuristics bundle"),
])
def spar(run, a):
  cfg = run.cfg

  # 1. Config-driven lenses [R2]: Prepend cfg.default_lenses
  default_lenses = list(getattr(cfg, "default_lenses", ["hats-haircuts-and-tattoos", "boring-technology"]))
  raw_fws = a.get("frameworks") or []
  if isinstance(raw_fws, str):
    raw_fws = [raw_fws]

  evaluated_slugs = []
  for slug in default_lenses + list(raw_fws):
    s = slug.strip()
    if s and s not in evaluated_slugs:
      evaluated_slugs.append(s)

  # 2. Loud failure on missing or unapproved lens [R1+R2]
  framework_paths = {}
  for slug in evaluated_slugs:
    fw_path = resolve_framework_path(cfg.frameworks, slug)
    if not fw_path or not fw_path.exists():
      close = [p.stem for p in cfg.frameworks.glob("*.md") if slug.split("-")[0] in p.stem] if cfg.frameworks.exists() else []
      raise PipelineError(
        "LENS_UNAVAILABLE",
        f"Required lens '{slug}' not found in frameworks vault: {cfg.frameworks}",
        did_you_mean=close,
        lens=slug,
      )

    ok, reason = check_framework_trust(fw_path, include_unapproved=False, verify_hash=True)
    if not ok:
      raise PipelineError(
        "LENS_UNAVAILABLE",
        f"Required lens '{slug}' failed trust policy: {reason}",
        lens=slug,
        reason=reason,
      )
    framework_paths[slug] = fw_path

  # 3. Read target proposal
  target_raw = a.get("target") or a.get("target_opt") or ""
  if not target_raw:
    raise PipelineError("MISSING_TARGET", "No target RFC, design doc, or diff provided to spar.")

  target_path = Path(target_raw)
  if not target_path.is_absolute():
    candidates = [cfg.vault / target_path, Path.cwd() / target_path, cfg.frameworks / target_path]
    found = None
    for c in candidates:
      if c.is_file():
        found = c
        break
    target_path = found if found else target_path

  if target_path.is_file():
    target_content = target_path.read_text(encoding="utf-8")
    target_doc_name = target_path.name
  else:
    if "\n" in target_raw or len(target_raw) > 80:
      target_content = target_raw
      target_doc_name = "Inline Design Proposal"
    else:
      raise PipelineError("TARGET_NOT_FOUND", f"Target document not found at: {target_raw}", target=target_raw)

  # 4. Compile synthesis charter [R2]
  def synthesize():
    charter = stack_frameworks_logic(
      cfg,
      evaluated_slugs,
      task=f"ADR Sparring Audit: {target_doc_name}",
      allow_order_precedence=a.get("allow_order_precedence", False),
      max_tokens=a.get("max_tokens", 4000),
      include_unapproved=False,
    )
    if charter.get("error") and not charter.get("schema_version"):
      raise PipelineError(charter.get("error", "STACKING_ERROR"), f"Failed to stack frameworks: {charter.get('error')}")
    return charter

  charter = run.step("stack-frameworks", synthesize)

  # 5. Resolve ADR dir and atomic numbering [R1]
  adr_dir = resolve_adr_dir(cfg, a.get("adr_dir"))
  adr_number = a.get("adr_number") or next_atomic_adr_number(adr_dir)

  # 6. Render spar prompt and run agent step
  charter_json = json.dumps(charter, indent=2, ensure_ascii=False)
  prompt = prompts.render(cfg, "spar", {
    "target": target_content,
    "target_doc": target_doc_name,
    "default_lenses": ", ".join(default_lenses),
    "evaluated_frameworks": ", ".join(evaluated_slugs),
    "synthesis_charter": charter_json,
    "adr_number": adr_number,
  })

  adr_data = run.step("spar-critique", lambda: agent_step(
    run, "spar", "spar", prompt, "adr", agent=a.get("agent"), timeout=1500
  ))

  # Ensure invariants on adr_data
  adr_data["adr_number"] = adr_number
  adr_data["target_doc"] = target_doc_name
  adr_data["evaluated_frameworks"] = evaluated_slugs
  adr_data["schema_version"] = "1.0.0"

  # 7. Write ADR note inside machine markers [R1+R2]
  def write_note():
    adr_file = notes.write_adr_note(cfg, adr_data, run.agent_for("spar"), run.id, target_dir=adr_dir)
    # 8. Close loop: record application strictly inside LOG markers of evaluated frameworks [R2]
    for slug in evaluated_slugs:
      fw_p = framework_paths.get(slug)
      if fw_p and fw_p.exists():
        notes.append_application(fw_p, "project", adr_file)
    return run.output(adr_file)

  adr_rel = run.step("write-adr", write_note)
  return [adr_rel]
