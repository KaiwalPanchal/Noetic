"""Knowledge layer: Knowledge graph and contradiction tracking across cognitive frameworks.

Captures opposing trade-offs, dialectic tensions, and contradictions identified during
framework stacking (Mode A) and sparring (Mode B) [R1].

Records persistent contradiction records in:
- frameworks/.index/contradictions.json
- frameworks/.index/graph.json
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from noetic.knowledge.config import Config, slugify


def _resolve_frameworks_dir(cfg: Any) -> Path:
  if hasattr(cfg, "frameworks") and cfg.frameworks is not None:
    return Path(cfg.frameworks)
  if isinstance(cfg, Path):
    if (cfg / "frameworks").is_dir():
      return cfg / "frameworks"
    return cfg
  return Path(str(cfg))


def _resolve_index_dir(cfg: Any) -> Path:
  fw_dir = _resolve_frameworks_dir(cfg)
  index_dir = fw_dir / ".index"
  index_dir.mkdir(parents=True, exist_ok=True)
  return index_dir


def record_contradiction(
    cfg: Any,
    framework_a: str,
    framework_b: str,
    tension_point: str,
    competing_heuristics: list[str] | None = None,
    source: str = "manual",
) -> dict[str, Any]:
  """Records a persistent contradiction record between two frameworks [R1].
  
  Saved in frameworks/.index/contradictions.json with:
  - framework_a
  - framework_b
  - tension_point
  - competing_heuristics
  """
  fw_a = slugify(framework_a.strip()) if framework_a else "unknown"
  fw_b = slugify(framework_b.strip()) if framework_b else "unknown"

  # Normalize ordering so (fw1, fw2) and (fw2, fw1) represent the same contradiction
  if fw_a > fw_b:
    fw_a, fw_b = fw_b, fw_a

  clean_tension = tension_point.strip()
  c_id = hashlib.sha256(f"{fw_a}:{fw_b}:{clean_tension.lower()}".encode("utf-8")).hexdigest()[:16]

  now_iso = datetime.now(timezone.utc).isoformat()
  heuristics = list(competing_heuristics or [])

  record = {
      "id": c_id,
      "framework_a": fw_a,
      "framework_b": fw_b,
      "tension_point": clean_tension,
      "competing_heuristics": heuristics,
      "source": source,
      "recorded_at": now_iso,
  }

  index_dir = _resolve_index_dir(cfg)
  contradictions_file = index_dir / "contradictions.json"

  records: list[dict[str, Any]] = []
  if contradictions_file.exists():
    try:
      raw = json.loads(contradictions_file.read_text(encoding="utf-8"))
      if isinstance(raw, list):
        records = raw
      elif isinstance(raw, dict) and "contradictions" in raw:
        records = raw["contradictions"]
    except Exception:
      records = []

  # Update if exists, else append
  found = False
  for idx, r in enumerate(records):
    if r.get("id") == c_id or (
        r.get("framework_a") == fw_a
        and r.get("framework_b") == fw_b
        and r.get("tension_point", "").lower() == clean_tension.lower()
    ):
      records[idx] = {**r, **record, "competing_heuristics": list(set(r.get("competing_heuristics", []) + heuristics))}
      found = True
      break

  if not found:
    records.append(record)

  contradictions_file.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

  # Also synchronize graph.json
  _sync_graph_json(cfg, records)

  return record


def record_tensions_from_charter(
    cfg: Any,
    charter: dict[str, Any],
    source: str = "stack_frameworks",
) -> list[dict[str, Any]]:
  """Captures opposing trade-offs and tension points identified during stack_frameworks or spar [R1]."""
  recorded: list[dict[str, Any]] = []

  # 1. Capture unresolved tensions (competing heuristics in same tier/domain)
  for tension in charter.get("unresolved_tensions", []):
    fws = tension.get("conflicting_frameworks", [])
    if len(fws) >= 2:
      fw_a, fw_b = fws[0], fws[1]
    elif len(fws) == 1:
      fw_a, fw_b = fws[0], "unknown"
    else:
      continue

    tension_point = tension.get("tension_dimension", "Opposing heuristic directives")
    heuristics = tension.get("conflicting_heuristics", [])
    rec = record_contradiction(
        cfg,
        framework_a=fw_a,
        framework_b=fw_b,
        tension_point=tension_point,
        competing_heuristics=heuristics,
        source=source,
    )
    recorded.append(rec)

  # 2. Capture resolved collisions (directional trade-offs resolved by hierarchy)
  for collision in charter.get("resolved_collisions", []):
    fws = collision.get("frameworks_involved", [])
    if len(fws) >= 2:
      fw_a, fw_b = fws[0], fws[1]
      dim = collision.get("collision_dimension", "Tier collision trade-off")
      winner = collision.get("winning_framework", "")
      rationale = collision.get("tier_domain_rationale", "")
      heuristics = [f"Winner: {winner}. Rationale: {rationale}"]
      rec = record_contradiction(
          cfg,
          framework_a=fw_a,
          framework_b=fw_b,
          tension_point=f"Collision ({dim})",
          competing_heuristics=heuristics,
          source=f"{source}_collision",
      )
      recorded.append(rec)

  return recorded


def get_contradictions(cfg: Any, framework: str | None = None) -> list[dict[str, Any]]:
  """Retrieves stored contradiction records, optionally filtered by framework slug [R1]."""
  index_dir = _resolve_index_dir(cfg)
  contradictions_file = index_dir / "contradictions.json"

  if not contradictions_file.exists():
    return []

  try:
    data = json.loads(contradictions_file.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "contradictions" in data:
      records = data["contradictions"]
    elif isinstance(data, list):
      records = data
    else:
      records = []
  except Exception:
    return []

  if not framework:
    return records

  target = slugify(framework.strip())
  return [
      r for r in records
      if slugify(r.get("framework_a", "")) == target or slugify(r.get("framework_b", "")) == target
  ]


def _sync_graph_json(cfg: Any, contradictions: list[dict[str, Any]]) -> None:
  """Maintains frameworks/.index/graph.json with nodes, edges, and contradictions."""
  index_dir = _resolve_index_dir(cfg)
  graph_file = index_dir / "graph.json"
  fw_dir = _resolve_frameworks_dir(cfg)

  nodes = []
  if fw_dir.exists():
    for md_file in fw_dir.glob("*.md"):
      if md_file.name.lower() in ("readme.md", "summary.md"):
        continue
      slug = md_file.stem
      nodes.append({
          "id": slug,
          "label": slug,
          "type": "framework",
          "path": str(md_file),
      })

  edges = []
  for c in contradictions:
    edges.append({
        "id": c.get("id"),
        "source": c.get("framework_a"),
        "target": c.get("framework_b"),
        "type": "contradiction",
        "tension_point": c.get("tension_point"),
    })

  graph_payload = {
      "schema_version": "1.0.0",
      "nodes": nodes,
      "edges": edges,
      "contradictions": contradictions,
  }
  graph_file.write_text(json.dumps(graph_payload, indent=2, ensure_ascii=False), encoding="utf-8")


def build_or_update_graph(cfg: Any) -> dict[str, Any]:
  """Scans framework notes and contradictions to assemble complete knowledge graph."""
  contradictions = get_contradictions(cfg)
  _sync_graph_json(cfg, contradictions)
  index_dir = _resolve_index_dir(cfg)
  graph_file = index_dir / "graph.json"
  return json.loads(graph_file.read_text(encoding="utf-8"))
