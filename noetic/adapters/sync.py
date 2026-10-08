"""noetic sync: render the canonical sources through the selected adapters into a vault.

Idempotent (no timestamps; running twice yields no diff), never touches user text outside
the managed block of CLAUDE.md / AGENTS.md / GEMINI.md, and never overwrites a file it did
not generate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re

from .antigravity import AntigravityAdapter
from .base import HEADER_PREFIX, Adapter, Canonical, apply_block
from .claude import ClaudeAdapter
from .codex import CodexAdapter
from .gemini import GeminiAdapter
from .universal import UniversalAdapter
from noetic.orchestration.loader import resource_dirs

CONFIG_NAME = "taste-engine.config.json"
PKG_DIR = Path(__file__).resolve().parents[1]  # .../noetic
ENGINE_DIR = PKG_DIR
AGENTS_DIR = PKG_DIR / "agents"  # agent contracts (names starting with `_` are shared fragments, not agents)
SEED_DIR = PKG_DIR / "seed"

REGISTRY: dict[str, type[Adapter]] = {
  "claude": ClaudeAdapter,
  "codex": CodexAdapter,
  "gemini": GeminiAdapter,
  "antigravity": AntigravityAdapter,
  "universal": UniversalAdapter,
}
ALIASES = {"agy": "antigravity", "claude-code": "claude", "agents": "universal", "agents.md": "universal"}
CONSTITUTION = "AGENTS.block.md"


@dataclass
class FileResult:
  path: str
  action: str  # created | updated | unchanged | skipped | removed
  adapter: str = ""
  detail: str = ""


@dataclass
class SyncReport:
  vault: Path
  agents: list[str]
  dry_run: bool = False
  files: list[FileResult] = field(default_factory=list)
  notes: list[str] = field(default_factory=list)

  @property
  def changed(self) -> list[FileResult]:
    return [f for f in self.files if f.action in ("created", "updated", "removed")]

  def summary(self) -> str:
    counts: dict[str, int] = {}
    for f in self.files:
      counts[f.action] = counts.get(f.action, 0) + 1
    return ", ".join(f"{n} {a}" for a, n in sorted(counts.items())) or "nothing to do"


def resolve_agents(agents: list[str] | None, cfg: dict) -> list[str]:
  chosen = agents if agents else cfg.get("adapters") or ["claude", "codex", "gemini", "antigravity"]
  if isinstance(chosen, str):
    chosen = [s for s in chosen.split(",")]
  out: list[str] = []
  for a in chosen:
    name = ALIASES.get(a.strip().lower(), a.strip().lower())
    if name == "all":
      return ["claude", "codex", "gemini", "antigravity"]
    if name not in REGISTRY:
      raise ValueError(f"unknown agent '{a}' (known: {', '.join(sorted(REGISTRY))})")
    if name not in out:
      out.append(name)
  return out


def _values(cfg: dict) -> dict[str, str]:
  owner = cfg.get("owner") or "Owner"
  paths = {"engine": "taste-engine", "frameworks": "frameworks", "twitter": "Twitter", "overmind": None,
           **(cfg.get("paths") or {})}
  return {"owner": owner, "owner_slug": re.sub(r"[^\w-]+", "-", owner.lower()).strip("-"),
          "agent": cfg.get("agent") or "Claude Code", **{k: v or "" for k, v in paths.items()}}


def load_canonical(vault: Path, cfg: dict | None = None, source: Path | None = None) -> Canonical:
  """Canonical lookup: explicit `source` dir (commands/, agents/, AGENTS.block.md), else the vault's
  own `<engine>/canonical` copy, else the source tree: noetic/agents/*.md plus every
  workflows/*/commands/*.md found by the workflow loader, with seed/ for the constitution."""
  cfg = cfg if cfg is not None else read_config(vault)
  values = _values(cfg)
  if source is None:
    installed = vault / values["engine"] / "canonical"
    source = installed if (installed / "commands").is_dir() else None
  if source is not None:
    commands, agents = [source / "commands"], [source / "agents"]
    constitution = source / CONSTITUTION
    if not constitution.exists():
      constitution = SEED_DIR / CONSTITUTION
  else:
    commands, agents = list(resource_dirs("commands")), [AGENTS_DIR]
    constitution = SEED_DIR / CONSTITUTION
  if not constitution.exists():
    raise FileNotFoundError(f"constitution block not found: {constitution}")
  return Canonical.load(commands, agents, constitution, values)


def read_config(vault: Path) -> dict:
  p = vault / CONFIG_NAME
  return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _read(path: Path) -> str | None:
  return path.read_bytes().decode("utf-8") if path.exists() else None


def _prune(vault: Path, adapters: list[Adapter], produced: set[str], report: SyncReport, dry_run: bool) -> None:
  for ad in adapters:
    for d in ad.managed_dirs:
      root = vault / d
      if not root.is_dir():
        continue
      for f in sorted(root.rglob("*")):
        rel = f.relative_to(vault).as_posix()
        if not f.is_file() or rel in produced:
          continue
        if HEADER_PREFIX in f.read_bytes()[:800].decode("utf-8", "replace"):
          report.files.append(FileResult(rel, "removed", ad.name, "no longer in canonical sources"))
          if not dry_run:
            f.unlink()
            parent = f.parent
            while parent != root and not any(parent.iterdir()):
              parent.rmdir()
              parent = parent.parent


def sync(vault: Path, agents: list[str] | None = None, *, dry_run: bool = False,
         source: Path | None = None) -> SyncReport:
  vault = Path(vault)
  cfg = read_config(vault)
  names = resolve_agents(agents, cfg)
  canon = load_canonical(vault, cfg, source)
  adapters = [REGISTRY[n]() for n in names]
  report = SyncReport(vault, names, dry_run)
  legacy_texts = {i.text for i in canon.commands + canon.agents}

  planned: dict[str, tuple] = {}
  for ad in adapters:
    if not ad.detect(vault):
      report.notes.append(f"{ad.name}: not detected in vault yet; generating anyway")
    report.notes += list(ad.notes)
    for out in ad.render(canon):
      prev = planned.get(out.path)
      if prev and prev[0].content != out.content:
        raise ValueError(f"adapters {prev[0].adapter} and {out.adapter} disagree on {out.path}")
      planned.setdefault(out.path, (out, ad.name))

  for rel, (out, adname) in planned.items():
    path = vault / rel
    existing = _read(path)
    if out.mode == "block":
      new = apply_block(existing, out.content, out.preamble)
    else:
      new = out.content
      if existing is not None and HEADER_PREFIX not in existing[:800] \
         and existing.replace("\r\n", "\n") not in legacy_texts:
        report.files.append(FileResult(rel, "skipped", adname, "exists and was not generated by noetic"))
        continue
    if existing == new:
      report.files.append(FileResult(rel, "unchanged", adname))
      continue
    report.files.append(FileResult(rel, "created" if existing is None else "updated", adname))
    if not dry_run:
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_bytes(new.encode("utf-8"))

  _prune(vault, adapters, set(planned), report, dry_run)
  return report
