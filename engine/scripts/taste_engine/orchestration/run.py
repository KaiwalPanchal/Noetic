"""Orchestration layer: run state on disk (pause / resume, stateless reducer).

One Run = one pipeline execution, saved at .taste-engine/runs/<run-id>.json.
Each finished step's output is cached there, so re-running the same run
(`resume`) skips the finished steps and continues from the failure.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import secrets

from taste_engine.knowledge.config import Config, slugify


class PipelineError(Exception):
  """A step failed. The message is a compact JSON diagnostic (12-factor #9)."""

  def __init__(self, code: str, detail: str = "", **extra):
    self.payload = {"status": "error", "code": code, "detail": detail[:300], **extra}
    super().__init__(json.dumps(self.payload, ensure_ascii=False))


class Run:
  def __init__(self, cfg: Config, command: str, args: dict, run_id: str | None = None):
    self.cfg = cfg
    self.dir = cfg.state_dir / "runs"
    self.dir.mkdir(parents=True, exist_ok=True)
    if run_id:
      self.path = self.dir / f"{run_id}.json"
      self.state = json.loads(self.path.read_text(encoding="utf-8"))
      self.state["status"] = "running"
    else:
      first = next((v for v in args.values() if isinstance(v, str) and v), command)
      label = slugify(first)[:30] or command
      run_id = f"{datetime.now():%Y%m%d-%H%M}-{command}-{label}-{secrets.token_hex(2)}"
      self.path = self.dir / f"{run_id}.json"
      self.state = {"id": run_id, "command": command, "args": args, "status": "running",
                    "created": datetime.now().isoformat(timespec="seconds"), "steps": {}, "outputs": []}
    self.id = self.state["id"]
    self.save()

  def save(self):
    self.state["updated"] = datetime.now().isoformat(timespec="seconds")
    self.path.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")

  def step(self, name: str, fn):
    """Run a step once; a resumed run reuses the cached result."""
    cached = self.state["steps"].get(name)
    if cached and cached.get("status") == "done":
      print(f"  ↺ {name} (cached)")
      return cached["output"]
    print(f"  ▸ {name} …", flush=True)
    self.state["steps"][name] = {"status": "running", "attempts": []}
    self.save()
    try:
      output = fn()
    except PipelineError as exc:
      self.state["steps"][name]["status"] = "failed"
      self.state.update(status="failed", error=exc.payload)
      self.save()
      raise
    self.state["steps"][name].update(status="done", output=output)
    self.save()
    return output

  def log_attempt(self, step: str, info: dict):
    self.state["steps"].setdefault(step, {}).setdefault("attempts", []).append(info)
    self.save()

  def set_agent(self, step: str, agent: str):
    self.state["steps"].setdefault(step, {})["agent"] = agent
    self.save()

  def add_notes(self, step: str, agent: str, notes: list[str]):
    """Gaps or assumptions an agent reported instead of improvising (contract rule 5)."""
    if notes:
      self.state.setdefault("harness_notes", []).extend(f"[{step} · {agent}] {n}" for n in notes)
      self.save()
      for n in notes:
        print(f"    ⚑ {agent} flagged: {n[:160]}")

  @property
  def notes(self) -> list[str]:
    return self.state.get("harness_notes", [])

  def agent_for(self, step: str) -> str:
    return self.state["steps"].get(step, {}).get("agent", "agent")

  def output(self, path: Path) -> str:
    """Record a file this run produced; returns its vault-relative path."""
    try:
      rel = str(Path(path).relative_to(self.cfg.vault))
    except ValueError:
      rel = str(path)
    if rel not in self.state["outputs"]:
      self.state["outputs"].append(rel)
    self.save()
    return rel

  def finish(self, status: str = "pending_review"):
    self.state["status"] = status
    self.save()
