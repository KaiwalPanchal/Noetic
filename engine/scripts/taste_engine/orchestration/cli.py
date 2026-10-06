"""Orchestration layer: the command line, generated from the pipeline registry."""

from __future__ import annotations

import argparse
import json
import sys

from taste_engine.actions import gate
from taste_engine.knowledge.config import Config, load_config
from taste_engine.knowledge.context import resolve_vault_path
from taste_engine.orchestration.registry import PIPELINES, discover
from taste_engine.orchestration.run import PipelineError, Run
from taste_engine.tools.agents import AGENTS, available, run_agent


def execute(cfg: Config, command: str, args: dict, run_id: str | None = None):
  run = Run(cfg, command, args, run_id)
  print(f"run {run.id}")
  try:
    outputs = PIPELINES[command].fn(run, args)
  except PipelineError as exc:
    print(f"\n✗ FAILED: {exc}\n  Fix the cause, then: python pipeline.py resume {run.id}")
    sys.exit(1)
  run.finish()
  print("\n✓ Done. Waiting for your review (status: pending_review):")
  for o in outputs or []:
    print(f"  • {o}")
  print("  Approve with: python pipeline.py approve \"<file>\"  ·  nothing is ever posted automatically.")


def show_status(cfg: Config, run_id: str | None):
  runs_dir = cfg.state_dir / "runs"
  if run_id:
    print(json.dumps(json.loads((runs_dir / f"{run_id}.json").read_text(encoding="utf-8")), indent=2, ensure_ascii=False))
    return
  runs = sorted(runs_dir.glob("*.json"), reverse=True)[:15] if runs_dir.exists() else []
  if not runs:
    print("No runs yet.")
  for f in runs:
    s = json.loads(f.read_text(encoding="utf-8"))
    steps = " → ".join(f"{k}{'✓' if v.get('status') == 'done' else '✗' if v.get('status') == 'failed' else '…'}"
                       for k, v in s["steps"].items())
    print(f"{s['status']:<15} {s['id']}\n                {steps}")


def doctor(cfg: Config):
  schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"], "additionalProperties": False}
  print("Checking agent CLIs (a tiny real call each; costs a few cents):")
  for name in AGENTS:
    if not available(name):
      print(f"  {name:<7} ✗ not installed")
      continue
    res = run_agent(name, 'Return {"ok": true}.', schema, cwd=cfg.vault, timeout=180, model=cfg.models.get(name))
    mark = "✓ ready" if res.ok else f"✗ {res.error['code']}: {res.error['detail'][:90]}"
    print(f"  {name:<7} {mark} ({res.seconds}s)")
  print("\nRouting:", json.dumps(cfg.agents, ensure_ascii=False))


def list_everything(cfg: Config):
  print("PIPELINES (orchestration → pipelines/)")
  for kind in ("knowledge", "content", "code", "project"):
    rows = [p for p in PIPELINES.values() if p.kind == kind]
    for p in rows:
      routed = cfg.agents.get(p.name, "")
      print(f"  [{kind:<9}] {p.name:<10} {p.help}" + (f"  (agent: {routed})" if routed else ""))
  print("\nAGENTS (tools/agents.py)")
  for name in AGENTS:
    print(f"  {name:<7} {'installed' if available(name) else 'not installed'}")
  print("\nROUTING (taste-engine.config.json → agents)")
  for node, agent in cfg.agents.items():
    print(f"  {node:<12} {agent}")


def main():
  discover()
  p = argparse.ArgumentParser(prog="pipeline.py", description="Taste Engine: multi-agent, human-gated pipelines")
  sub = p.add_subparsers(dest="cmd", required=True)

  for pl in PIPELINES.values():
    sp = sub.add_parser(pl.name, help=f"[{pl.kind}] {pl.help}")
    for flags, kw in pl.args:
      sp.add_argument(*flags, **kw)
    if pl.agent_flag:
      sp.add_argument("--agent", choices=AGENTS, help="force one agent for this run (no fallback)")

  sp = sub.add_parser("approve", help="[gate] mark a generated note approved")
  sp.add_argument("file")
  sp = sub.add_parser("reject", help="[gate] mark a generated note rejected")
  sp.add_argument("file")
  sp.add_argument("--reason", default="")
  sp = sub.add_parser("status", help="list runs, or show one")
  sp.add_argument("run_id", nargs="?")
  sp = sub.add_parser("resume", help="re-run a failed run; finished steps are reused")
  sp.add_argument("run_id")
  sub.add_parser("doctor", help="check which agent CLIs work (tiny real calls)")
  sub.add_parser("list", help="show pipelines, agents and routing")

  args = p.parse_args()
  cfg = load_config()

  if args.cmd in PIPELINES:
    execute(cfg, args.cmd, {k: v for k, v in vars(args).items() if k != "cmd"})
  elif args.cmd in ("approve", "reject"):
    path = resolve_vault_path(cfg, args.file)
    if not path:
      sys.exit(f"Not found: {args.file}")
    (gate.approve(path) if args.cmd == "approve" else gate.reject(path, args.reason))
    print(f"✓ {path.relative_to(cfg.vault)} → {gate.status_of(path)}")
  elif args.cmd == "status":
    show_status(cfg, args.run_id)
  elif args.cmd == "resume":
    state = json.loads((cfg.state_dir / "runs" / f"{args.run_id}.json").read_text(encoding="utf-8"))
    execute(cfg, state["command"], state["args"], run_id=args.run_id)
  elif args.cmd == "doctor":
    doctor(cfg)
  elif args.cmd == "list":
    list_everything(cfg)
