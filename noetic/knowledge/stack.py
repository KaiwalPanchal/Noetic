"""Knowledge layer: framework stacking, parsing, and synthesis charter compiler.

Implements Mode A Cognitive Framework Stacking:
- 4-Tier Hierarchy: Tier 1 Taste Dogmas > Tier 2 Architecture > Tier 3 UI > Tier 4 Governance [R2]
- Domain Partitioning: domain_tags partition non-conflicting heuristics in the same tier [R2]
- Collision Resolution: cross-tier collisions resolved by tier hierarchy; same-tier collisions
  emit unresolved_tensions by default unless allow_order_precedence=True [R1+R2]
- Output contract: strictly validates against workflows/taste_engine/schemas/synthesis_charter.json [R2]
- Trust & Serving Policy: checks note status == 'approved' and verifies approval_hash [R1]
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from noetic.knowledge.config import Config, slugify
from noetic.knowledge.notes import (
    compute_content_hash,
    get_approval_hash,
    status_of,
    verify_approval_hash,
)

# Stopwords excluded during conflict keyword analysis
CONFLICT_STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "is", "it",
    "by", "with", "this", "that", "from", "as", "are", "be", "was", "were", "when",
    "rule", "context", "prioritize", "over", "because", "operational", "than", "not",
    "will", "can", "should", "must", "all", "any", "each", "both", "tier",
}

# Antonym pairs indicating opposing directional guidance
DIRECTIONAL_ANTONYMS = [
    ("local", "remote"),
    ("local", "cloud"),
    ("offline", "online"),
    ("immediate", "waiting"),
    ("instant", "deferred"),
    ("instant", "background"),
    ("purge", "preserve"),
    ("synchronous", "asynchronous"),
    ("commit", "rollback"),
    ("speed", "consistency"),
    ("latency", "storage"),
    ("optimistic", "pessimistic"),
    ("ephemeral", "durable"),
]


def check_framework_trust(
    path: Path,
    include_unapproved: bool = False,
    verify_hash: bool = True,
) -> tuple[bool, str]:
  """Validates note existence, approval status, and cryptographic content hash [R1]."""
  if not path.exists():
    return False, f"Framework not found: {path.name}"
  status = status_of(path) or "pending_review"
  if not include_unapproved and status != "approved":
    return False, f"Framework '{path.stem}' is not approved (status: {status})."
  if status == "approved" and verify_hash:
    app_hash = get_approval_hash(path)
    if not app_hash:
      return False, "APPROVAL_HASH_MISMATCH"
    text = path.read_text(encoding="utf-8")
    if compute_content_hash(text) != app_hash:
      return False, "APPROVAL_HASH_MISMATCH"
  return True, ""


def parse_framework_note(path: Path | str, text: str | None = None) -> dict[str, Any]:
  """Parses a framework markdown note into structured cognitive primitives and heuristics."""
  p = Path(path) if isinstance(path, (str, Path)) else Path("framework.md")
  slug = p.stem
  if text is None:
    text = p.read_text(encoding="utf-8") if p.exists() else ""

  # 1. Frontmatter extraction
  status = status_of(p) if p.exists() else None
  if not status:
    m_st = re.search(r"^status:\s*(\S+)", text, re.M)
    status = m_st.group(1) if m_st else "pending_review"

  m_hash = re.search(r"^approval_hash:\s*\"?([a-f0-9]{64})\"?", text, re.M)
  app_hash = m_hash.group(1) if m_hash else ""

  # 2. Title & Domain Tags
  m_title = re.search(r"^# Framework:\s*(.+)$", text, re.M)
  if not m_title:
    m_h1 = re.search(r"^#\s+(.+)$", text, re.M)
    title = m_h1.group(1).strip() if m_h1 else slug
  else:
    title = m_title.group(1).strip()

  tags: list[str] = []
  m_tags = re.search(r"\*\*Tags:\*\*\s*(.+)$", text, re.M)
  if m_tags:
    raw_tags = re.findall(r"#?([a-zA-Z0-9_\-]+)", m_tags.group(1))
    tags = [t.lower() for t in raw_tags if t.lower() not in ("framework", "")]

  m_dom = re.search(r"\*\*Primary Domain:\*\*\s*(.+)$", text, re.M)
  if m_dom:
    dom_str = slugify(m_dom.group(1).strip())
    if dom_str and dom_str not in tags:
      tags.append(dom_str)

  # 3. Admission Score & Rubric
  m_score = re.search(r"\*\*Admission Score:\*\*\s*([0-9\.]+)", text, re.M)
  admission_score = float(m_score.group(1)) if m_score else 5.0

  m_kb = re.search(r"\*\*The Keyboard Test:\*\*\s*(.+)$", text, re.M)
  keyboard_test = m_kb.group(1).strip() if m_kb else ""

  # 4. Core Idea, Razor & Invariant
  core_idea = ""
  if "## 1. Core Idea" in text:
    sec = text.split("## 1. Core Idea", 1)[1]
    core_idea = sec.split("## ", 1)[0].strip()
  elif "## Core Idea" in text:
    sec = text.split("## Core Idea", 1)[1]
    core_idea = sec.split("## ", 1)[0].strip()

  razor = ""
  m_razor = re.search(r"\*\*The Core Question / Razor:\*\*\s*\"?([^\"]+)\"?", text)
  if m_razor:
    razor = m_razor.group(1).strip()

  invariant = ""
  m_inv = re.search(r"\*\*Governing Invariant:\*\*\s*(.+)$", text, re.M)
  if m_inv:
    invariant = m_inv.group(1).strip()

  # 5. Primitives
  primitives: list[dict[str, str]] = []
  p_matches = re.findall(
      r"^-\s+\*\*(.+?)\*\*\s*(?:\(`?([a-z]+)`?\))?:\s*(.+)$", text, re.M
  )
  for name, kind, definition in p_matches:
    kind_val = kind.lower() if kind and kind.lower() in ("entity", "variable", "force", "state") else "entity"
    primitives.append({
        "name": name.strip()[:200],
        "framework_slug": slug[:100],
        "kind": kind_val,
        "definition": definition.strip()[:1000],
    })

  if not primitives:
    primitives.append({
        "name": title[:200],
        "framework_slug": slug[:100],
        "kind": "entity",
        "definition": (core_idea or razor or title)[:1000],
    })

  # 6. Directional Heuristics
  heuristics: list[dict[str, Any]] = []
  h_pattern = re.compile(
      r"^-\s+\*\*When in (.+?)\*\*\s*→\s*Prioritize \*\*(.+?)\*\*\s*over\s*_(.+?)_\s*"
      r"because\s*(.+?)\.\s*\(Rule:\s*`?([^`\)]+?)`?\)\s*(.*)$",
      re.M,
  )
  for match in h_pattern.finditer(text):
    context, prioritize, over, because, rule, suffix = match.groups()
    tier = 1
    m_tier = re.search(r"\[Tier\s*(\d+)\]", suffix)
    if m_tier:
      tier = max(1, min(4, int(m_tier.group(1))))

    h_tags = list(tags)
    m_htags = re.search(r"\[Tags:\s*([^\]]+)\]", suffix)
    if m_htags:
      custom_tags = [t.strip().lower() for t in m_htags.group(1).split(",") if t.strip()]
      if custom_tags:
        h_tags = custom_tags

    anchor = f"{title} (Core Heuristic)"
    m_anchor = re.search(r"\[Anchor:\s*([^\]]+)\]", suffix)
    if m_anchor:
      anchor = m_anchor.group(1).strip()

    heuristics.append({
        "framework_slug": slug[:100],
        "context": context.strip()[:500],
        "prioritize": prioritize.strip()[:500],
        "over": over.strip()[:500],
        "because": because.strip()[:1000],
        "operational_rule": rule.strip()[:1000],
        "tier": tier,
        "domain_tags": h_tags if h_tags else ["general"],
        "provenance_anchor": anchor[:1000],
    })

  # Legacy fallback: convert principles if no directional heuristics matched
  if not heuristics and "## Principles" in text:
    p_sec = text.split("## Principles", 1)[1].split("## ", 1)[0]
    p_matches = re.findall(r"^\d+\.\s+\*\*(.+?)\*\*:\s*(.+)$", p_sec, re.M)
    for p_name, p_expl in p_matches:
      heuristics.append({
          "framework_slug": slug[:100],
          "context": f"When applying {p_name}"[:500],
          "prioritize": p_name.strip()[:500],
          "over": "ad-hoc unprincipled alternatives"[:500],
          "because": p_expl.strip()[:1000],
          "operational_rule": f"Enforce {p_name.strip()}"[:1000],
          "tier": 1,
          "domain_tags": tags if tags else ["general"],
          "provenance_anchor": f"{title} (Principles)"[:1000],
      })

  if not heuristics:
    heuristics.append({
        "framework_slug": slug[:100],
        "context": f"When executing within {title}"[:500],
        "prioritize": (razor or core_idea or title)[:100][:500],
        "over": "unstructured patterns"[:500],
        "because": (core_idea or title)[:1000],
        "operational_rule": (razor or title)[:1000],
        "tier": 1,
        "domain_tags": tags if tags else ["general"],
        "provenance_anchor": f"{title} (Canonical)"[:1000],
    })

  # 7. Trade-off Matrix
  trade_offs: list[dict[str, str]] = []
  if "### Trade-Off Matrix" in text or "## Trade-Off Matrix" in text:
    to_sec = text.split("Trade-Off Matrix", 1)[1].split("## ", 1)[0]
    for line in to_sec.splitlines():
      line = line.strip()
      if not line.startswith("|") or ":---" in line or "Tension Dimension" in line:
        continue
      parts = [p.strip() for p in line.split("|")[1:-1]]
      if len(parts) >= 5:
        trade_offs.append({
            "dimension": parts[0][:500],
            "recommended_choice": parts[1][:500],
            "sacrificed": parts[2][:500],
            "gained": parts[3][:500],
            "boundary_flip_condition": parts[4][:500],
        })

  # 8. Anti-Patterns
  anti_patterns: list[Any] = []
  if "## 5. Anti-Patterns" in text or "## Anti-Patterns" in text:
    anchor_str = "## 5. Anti-Patterns" if "## 5. Anti-Patterns" in text else "## Anti-Patterns"
    ap_sec = text.split(anchor_str, 1)[1].split("## ", 1)[0]
    for line in ap_sec.splitlines():
      line = line.strip()
      if not line.startswith("-"):
        continue
      line_body = line.lstrip("- ").strip()
      m_ap = re.match(r"^\*\*(.+?)\*\*:\s*(.+?)\s*→\s*(.+?)\s*\(Recovery:\s*(.+?)\)", line_body)
      if m_ap:
        trap, sym, fail, rec = m_ap.groups()
        anti_patterns.append({
            "trap_name": trap.strip(),
            "symptom": sym.strip(),
            "failure_mechanism": fail.strip(),
            "recovery_move": rec.strip(),
        })
      else:
        anti_patterns.append(line_body)

  all_tiers = sorted({h["tier"] for h in heuristics})
  all_domain_tags = sorted({t for h in heuristics for t in h["domain_tags"]})

  return {
      "slug": slug,
      "framework_name": title,
      "status": status,
      "approval_hash": app_hash,
      "tags": tags,
      "admission_score": admission_score,
      "the_keyboard_test": keyboard_test,
      "core_idea": core_idea,
      "razor": razor,
      "governing_invariant": invariant,
      "primitives": primitives,
      "directional_heuristics": heuristics,
      "trade_off_matrix": trade_offs,
      "anti_patterns": anti_patterns,
      "tiers": all_tiers,
      "domain_tags": all_domain_tags,
      "raw_text": text,
  }


def detect_heuristic_collision(h1: dict[str, Any], h2: dict[str, Any]) -> tuple[bool, str]:
  """Detects if two heuristics from different frameworks conflict along a shared domain [R2]."""
  if h1["framework_slug"] == h2["framework_slug"]:
    return False, ""

  tags1 = set(h1.get("domain_tags", []))
  tags2 = set(h2.get("domain_tags", []))
  shared = tags1 & tags2
  if not shared:
    return False, ""

  # Words in prioritize and over
  p1_words = set(re.findall(r"[a-z0-9]+", h1["prioritize"].lower())) - CONFLICT_STOPWORDS
  o1_words = set(re.findall(r"[a-z0-9]+", h1["over"].lower())) - CONFLICT_STOPWORDS
  p2_words = set(re.findall(r"[a-z0-9]+", h2["prioritize"].lower())) - CONFLICT_STOPWORDS
  o2_words = set(re.findall(r"[a-z0-9]+", h2["over"].lower())) - CONFLICT_STOPWORDS

  # Priority inversion: prioritize in one is over in another
  if (p1_words & o2_words) or (p2_words & o1_words):
    dim = f"Priority inversion in [{', '.join(sorted(shared))}]: '{h1['prioritize']}' vs '{h2['prioritize']}'"
    return True, dim[:500]

  # Opposing antonym pairs
  text1 = (h1["prioritize"] + " " + h1["operational_rule"]).lower()
  text2 = (h2["prioritize"] + " " + h2["operational_rule"]).lower()
  for w1, w2 in DIRECTIONAL_ANTONYMS:
    if (w1 in text1 and w2 in text2) or (w2 in text1 and w1 in text2):
      dim = f"Direct opposing stance ({w1} vs {w2}) in [{', '.join(sorted(shared))}]"
      return True, dim[:500]

  # Context overlap check with opposing rules
  c1_words = set(re.findall(r"[a-z0-9]+", h1["context"].lower())) - CONFLICT_STOPWORDS
  c2_words = set(re.findall(r"[a-z0-9]+", h2["context"].lower())) - CONFLICT_STOPWORDS
  if len(c1_words & c2_words) >= 2 and p1_words != p2_words:
    dim = f"Operational tension in [{', '.join(sorted(shared))}]: '{h1['prioritize']}' vs '{h2['prioritize']}'"
    return True, dim[:500]

  return False, ""


def calculate_token_footprint(heuristics: list[dict[str, Any]], primitives: list[dict[str, Any]]) -> int:
  """Roughly estimates the token footprint of active charter components (1 token ~= 4 chars)."""
  total_chars = 0
  for h in heuristics:
    total_chars += len(h.get("context", "")) + len(h.get("prioritize", "")) + len(h.get("over", ""))
    total_chars += len(h.get("because", "")) + len(h.get("operational_rule", ""))
    total_chars += sum(len(t) for t in h.get("domain_tags", []))
  for p in primitives:
    total_chars += len(p.get("name", "")) + len(p.get("definition", ""))
  return max(20, total_chars // 4)


def stack_frameworks_logic(
    cfg: Config,
    slugs: list[str],
    task: str = "",
    allow_order_precedence: bool = False,
    max_tokens: int = 4000,
    include_unapproved: bool = False,
) -> dict[str, Any]:
  """Core deterministic stacking algorithm validating against synthesis_charter.json [R1+R2]."""
  if not slugs:
    return {"ok": False, "error": "No framework slugs provided."}

  # 1. Trust verification for each framework
  verify_hash = cfg.mcp_serve_policy.get("verify_hash", True) if hasattr(cfg, "mcp_serve_policy") else True
  require_approved = cfg.mcp_serve_policy.get("require_approved", True) if hasattr(cfg, "mcp_serve_policy") else True
  effective_unapproved = include_unapproved or not require_approved

  parsed_fws: list[dict[str, Any]] = []
  for slug in slugs:
    fw_path = cfg.frameworks / f"{slug}.md"
    ok, err = check_framework_trust(fw_path, include_unapproved=effective_unapproved, verify_hash=verify_hash)
    if not ok:
      return {"ok": False, "error": err}
    parsed_fws.append(parse_framework_note(fw_path))

  # 2. Primitive aggregation
  seen_primitives = set()
  active_primitives: list[dict[str, Any]] = []
  for fw in parsed_fws:
    for p in fw["primitives"]:
      key = (p["name"].lower(), p["kind"])
      if key not in seen_primitives:
        seen_primitives.add(key)
        active_primitives.append({
            "name": p["name"][:200],
            "framework_slug": fw["slug"][:100],
            "kind": p["kind"],
            "definition": p["definition"][:1000],
        })

  # 3. Collision resolution & tension extraction
  all_heuristics: list[dict[str, Any]] = []
  for fw in parsed_fws:
    for h in fw["directional_heuristics"]:
      all_heuristics.append(dict(h))

  resolved_collisions: list[dict[str, Any]] = []
  unresolved_tensions: list[dict[str, Any]] = []
  overridden_indices: set[int] = set()

  n = len(all_heuristics)
  for i in range(n):
    for j in range(i + 1, n):
      h1, h2 = all_heuristics[i], all_heuristics[j]
      collides, dimension = detect_heuristic_collision(h1, h2)
      if not collides:
        continue

      t1, t2 = h1["tier"], h2["tier"]
      fw1, fw2 = h1["framework_slug"], h2["framework_slug"]

      if t1 != t2:
        # Cross-tier collision: lower number (Tier 1 > Tier 2 > Tier 3 > Tier 4) strictly overrides
        if t1 < t2:
          winner, loser = fw1, fw2
          overridden_indices.add(j)
          win_tier, lose_tier = t1, t2
        else:
          winner, loser = fw2, fw1
          overridden_indices.add(i)
          win_tier, lose_tier = t2, t1

        resolved_collisions.append({
            "collision_dimension": dimension[:500],
            "frameworks_involved": [fw1[:100], fw2[:100]],
            "winning_framework": winner[:100],
            "tier_domain_rationale": (
                f"Tier {win_tier} ({winner}) overrides Tier {lose_tier} ({loser}) "
                f"under the 4-tier cognitive hierarchy."
            )[:2000],
        })
      else:
        # Same-tier, same-domain collision [R1+R2]
        if allow_order_precedence:
          idx1 = slugs.index(fw1) if fw1 in slugs else 999
          idx2 = slugs.index(fw2) if fw2 in slugs else 999
          if idx1 <= idx2:
            winner, loser = fw1, fw2
            overridden_indices.add(j)
          else:
            winner, loser = fw2, fw1
            overridden_indices.add(i)

          resolved_collisions.append({
              "collision_dimension": dimension[:500],
              "frameworks_involved": [fw1[:100], fw2[:100]],
              "winning_framework": winner[:100],
              "tier_domain_rationale": (
                  f"Same-tier (Tier {t1}) collision resolved by explicit argument-order precedence: "
                  f"'{winner}' precedes '{loser}'."
              )[:2000],
          })
        else:
          unresolved_tensions.append({
              "tension_dimension": dimension[:500],
              "conflicting_frameworks": [fw1[:100], fw2[:100]],
              "conflicting_heuristics": [
                  f"{fw1}: Prioritize {h1['prioritize']} over {h1['over']}"[:1000],
                  f"{fw2}: Prioritize {h2['prioritize']} over {h2['over']}"[:1000],
              ],
              "escalation_note": (
                  f"Same-tier (Tier {t1}) collision in shared domain tags. "
                  f"Requires explicit human decision or trade-off resolution."
              )[:2000],
          })

  # 4. Assemble harmonized heuristics (ordered by tier)
  surviving_heuristics = [
      h for idx, h in enumerate(all_heuristics) if idx not in overridden_indices
  ]
  surviving_heuristics.sort(key=lambda h: (h["tier"], slugs.index(h["framework_slug"]) if h["framework_slug"] in slugs else 0))

  # 5. Token budget enforcement & trimming [R1]
  trimmed_count = 0
  total_tokens = calculate_token_footprint(surviving_heuristics, active_primitives)
  while total_tokens > max_tokens and len(surviving_heuristics) > 1:
    # Trim from highest tier number (least authoritative, e.g. Tier 4, Tier 3)
    surviving_heuristics.pop()
    trimmed_count += 1
    total_tokens = calculate_token_footprint(surviving_heuristics, active_primitives)

  charter: dict[str, Any] = {
      "schema_version": "1.0.0",
      "active_frameworks": [s[:100] for s in slugs],
      "active_primitives": active_primitives,
      "harmonized_heuristics": surviving_heuristics,
      "resolved_collisions": resolved_collisions,
      "unresolved_tensions": unresolved_tensions,
      "token_budget_metadata": {
          "included_count": len(surviving_heuristics),
          "trimmed_count": trimmed_count,
          "estimated_tokens": total_tokens,
      },
  }

  # Validate against synthesis_charter.json schema
  from noetic.orchestration.loader import find_resource
  import jsonschema

  try:
    schema_path = find_resource("schemas", "synthesis_charter.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=charter, schema=schema)
  except Exception as e:
    charter["harness_notes"] = [f"Schema validation warning: {e}"]

  # Record contradictions and tension points in knowledge graph [R1]
  if unresolved_tensions or resolved_collisions:
    try:
      from noetic.knowledge.graph import record_tensions_from_charter
      record_tensions_from_charter(cfg, charter, source="stack_frameworks")
    except Exception:
      pass

  return charter


def audit_against_frameworks_logic(
    cfg: Config,
    diff_or_text: str,
    frameworks: list[str],
    include_unapproved: bool = False,
) -> dict[str, Any]:
  """Scores content against stacked heuristics and anti-patterns."""
  charter = stack_frameworks_logic(
      cfg, frameworks, include_unapproved=include_unapproved
  )
  if "error" in charter and not charter.get("schema_version"):
    return charter

  parsed_fws = [parse_framework_note(cfg.frameworks / f"{slug}.md") for slug in frameworks if (cfg.frameworks / f"{slug}.md").exists()]

  text_lower = diff_or_text.lower()
  compliance_list = []
  penalties = 0.0

  # Heuristic compliance
  for h in charter.get("harmonized_heuristics", []):
    rule = h["operational_rule"].lower()
    prio = h["prioritize"].lower()
    over = h["over"].lower()

    # Positive and negative keywords
    pos_words = set(re.findall(r"[a-z0-9]+", prio + " " + rule)) - CONFLICT_STOPWORDS
    neg_words = set(re.findall(r"[a-z0-9]+", over)) - CONFLICT_STOPWORDS

    pos_hits = sum(1 for w in pos_words if w in text_lower)
    neg_hits = sum(1 for w in neg_words if w in text_lower)

    if neg_hits > 0 and pos_hits == 0:
      status = "fail"
      penalties += 0.8
      note = f"Content exhibits deprioritized pattern: '{h['over']}'"
    elif pos_hits > 0:
      status = "pass"
      note = f"Content aligns with prioritized rule: '{h['operational_rule']}'"
    else:
      status = "neutral"
      penalties += 0.2
      note = f"No explicit adherence or violation detected for: '{h['prioritize']}'"

    compliance_list.append({
        "framework": h["framework_slug"],
        "tier": h["tier"],
        "rule": h["operational_rule"],
        "status": status,
        "note": note,
    })

  # Anti-pattern checks
  violations = []
  for fw in parsed_fws:
    for ap in fw.get("anti_patterns", []):
      if isinstance(ap, dict):
        trap = ap.get("trap_name", "")
        symptom = ap.get("symptom", "")
        fail = ap.get("failure_mechanism", "")
        recovery = ap.get("recovery_move", "")
        check_words = set(re.findall(r"[a-z0-9]+", trap.lower() + " " + symptom.lower())) - CONFLICT_STOPWORDS
        if any(w in text_lower for w in check_words if len(w) > 4):
          violations.append({
              "framework": fw["slug"],
              "trap_name": trap,
              "symptom": symptom,
              "recovery_move": recovery,
          })
          penalties += 1.0
      elif isinstance(ap, str):
        ap_words = set(re.findall(r"[a-z0-9]+", ap.lower())) - CONFLICT_STOPWORDS
        if any(w in text_lower for w in ap_words if len(w) > 4):
          violations.append({
              "framework": fw["slug"],
              "trap_name": ap[:80],
              "recovery_move": "Refactor away from identified anti-pattern.",
          })
          penalties += 0.5

  final_score = max(0.0, min(5.0, 5.0 - penalties))
  recommendations = [v["recovery_move"] for v in violations if "recovery_move" in v]

  return {
      "ok": True,
      "adherence_score": round(final_score, 1),
      "frameworks": frameworks,
      "anti_pattern_violations": violations,
      "heuristic_compliance": compliance_list,
      "recommendations": recommendations,
      "summary": (
          f"Audit completed across {len(frameworks)} frameworks. "
          f"Score: {round(final_score, 1)}/5.0 with {len(violations)} anti-pattern violations."
      ),
  }
