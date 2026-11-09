"""Knowledge layer: framework deduplication and embedding graph intelligence.

Implements 3-tier framework deduplication:
- Tier 1: Slug matching with length/slug guards (avoids false merges on short slugs e.g. "ui", "c4") [R1]
- Tier 2: Embedding comparison against existing frameworks (identical merge vs cousin wikilinks) [R1+R2]
- Tier 3: Novel framework creation

Embedding cache in SQLite at `<vault>/.noetic/embeddings.db` keyed by:
sha256(core_text + ":" + provider + ":" + model + ":" + version) [R1+R2]
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
from typing import Callable

from noetic.knowledge.config import Config, slugify

# Guarded short slugs that should never match strictly on slug equality [R1]
SHORT_SLUG_GUARDS = {
    "ui", "c4", "db", "ai", "qa", "mvp", "api", "cli", "dev", "ops", "sdk", "app",
    "ml", "id", "os", "ux", "io", "v1", "v2", "p0", "p1", "p2", "pr", "ad",
}

# Stopwords excluded during deterministic vectorization to eliminate template noise
TEMPLATE_STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "is", "it",
    "by", "with", "this", "that", "from", "as", "are", "be", "was", "were", "when",
    "entity", "heuristic", "context", "prioritize", "over", "because", "rule", "trade",
    "off", "dimension", "choice", "sacrificed", "gained", "flip", "matrix", "primitive",
}


def core_semantic_text(framework_data: dict) -> str:
    """Extracts ONLY ontology entities, directional heuristics, and trade-off matrix for vector/dedup [R2]."""
    parts = []

    # 1. Ontology entities & primitives & governing invariant
    ontology = framework_data.get("ontology")
    if isinstance(ontology, dict):
        primitives = ontology.get("primitives", [])
        for p in primitives:
            if isinstance(p, dict):
                parts.append(f"entity: {p.get('name', '')}: {p.get('definition', '')}")
            elif isinstance(p, str):
                parts.append(f"entity: {p}")
        inv = ontology.get("governing_invariant")
        if inv:
            parts.append(f"invariant: {inv}")
    elif "entities" in framework_data and isinstance(framework_data["entities"], list):
        for e in framework_data["entities"]:
            parts.append(f"entity: {e}")

    # 2. Directional heuristics
    heuristics = framework_data.get("directional_heuristics", [])
    if isinstance(heuristics, list):
        for h in heuristics:
            if isinstance(h, dict):
                parts.append(
                    f"heuristic: in {h.get('context', '')} prioritize {h.get('prioritize', '')} over "
                    f"{h.get('over', '')} because {h.get('because', '')} rule: {h.get('operational_rule', '')}"
                )
            elif isinstance(h, str):
                parts.append(f"heuristic: {h}")

    # 3. Trade-off matrix
    trade_offs = framework_data.get("trade_off_matrix", [])
    if isinstance(trade_offs, list):
        for t in trade_offs:
            if isinstance(t, dict):
                parts.append(
                    f"trade-off: {t.get('dimension', '')}: recommend {t.get('recommended_choice', '')} "
                    f"sacrifice {t.get('sacrificed', '')} gain {t.get('gained', '')} "
                    f"flip: {t.get('boundary_flip_condition', '')}"
                )
            elif isinstance(t, str):
                parts.append(f"trade-off: {t}")

    # Legacy fallback if none of the above were present
    if not parts:
        principles = framework_data.get("principles", [])
        if isinstance(principles, list):
            for p in principles:
                if isinstance(p, dict):
                    parts.append(f"principle: {p.get('name', '')}: {p.get('explanation', '')}")
                elif isinstance(p, str):
                    parts.append(f"principle: {p}")
        for m in framework_data.get("mental_moves", []):
            parts.append(f"move: {m}")
        if framework_data.get("core_idea"):
            parts.append(f"core: {framework_data['core_idea']}")

    return "\n".join(parts).strip()


def extract_semantic_text_from_markdown(text: str) -> str:
    """Extracts core semantic content from a framework markdown note."""
    if "<!-- NOETIC:AUTO:START -->" in text and "<!-- NOETIC:AUTO:END -->" in text:
        text = text.split("<!-- NOETIC:AUTO:START -->", 1)[1].split("<!-- NOETIC:AUTO:END -->", 1)[0]
    elif text.startswith("---") and "\n---" in text[3:]:
        end = text.index("\n---", 3)
        text = text[end + 4:]

    lines = []
    capture = True
    for line in text.splitlines():
        if line.startswith("## Applications Log") or line.startswith("<!-- NOETIC:LOG:START -->") or line.startswith("<!-- NOETIC:PROPOSED:START -->"):
            break
        if line.startswith("## ") or line.startswith("# "):
            header = line.lower()
            capture = any(k in header for k in ("core", "heuristic", "procedure", "move", "where to apply", "trade-off", "anti-pattern", "framework"))
        if capture and line.strip() and not line.startswith("```"):
            lines.append(line.strip())

    return "\n".join(lines).strip()


def make_cache_key(core_text: str, provider: str, model: str, version: str) -> str:
    """sha256(core_text + ":" + provider + ":" + model + ":" + version) [R1+R2]."""
    payload = f"{core_text}:{provider}:{model}:{version}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def get_embedding_db_path(cfg: Config) -> Path:
    state_dir = getattr(cfg, "state_dir", cfg.vault / ".noetic")
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "embeddings.db"


def init_embedding_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            cache_key TEXT PRIMARY KEY,
            vector TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            version TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculates cosine similarity between two float vectors in [0.0, 1.0]."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    sim = dot / (norm1 * norm2)
    return max(0.0, min(1.0, sim))


def deterministic_vector(text: str, dim: int = 2048) -> list[float]:
    """Generates a stable, cross-process deterministic normalized vector from tokens and character n-grams.
    
    Provides offline deterministic cosine similarity for testing, calibration, and zero-dependency operation.
    """
    words = [w for w in re.findall(r"\b[a-z]{2,}\b", text.lower()) if w not in TEMPLATE_STOPWORDS]
    if not words:
        return [0.0] * dim

    features = list(words)
    for w in words:
        if len(w) >= 3:
            for i in range(len(w) - 2):
                features.append(w[i:i+3])
        if len(w) >= 4:
            for i in range(len(w) - 3):
                features.append(w[i:i+4])

    counts = Counter(features)
    vec = [0.0] * dim
    for feat, count in counts.items():
        h = int(hashlib.sha256(feat.encode("utf-8")).hexdigest()[:8], 16) % dim
        vec[h] += 1.0 + math.log(count)

    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm > 0 else vec


def get_embedding(text: str, cfg: Config | None = None, force_refresh: bool = False) -> list[float]:
    """Retrieves or calculates vector embedding with SQLite caching [R1+R2]."""
    emb_cfg = getattr(cfg, "embedding_model", {"provider": "openai", "model": "text-embedding-3-small", "version": "1"}) if cfg else {
        "provider": "openai", "model": "text-embedding-3-small", "version": "1"
    }
    provider = str(emb_cfg.get("provider", "openai"))
    model = str(emb_cfg.get("model", "text-embedding-3-small"))
    version = str(emb_cfg.get("version", "1"))

    cache_key = make_cache_key(text, provider, model, version)
    db_path = get_embedding_db_path(cfg) if cfg else Path(".noetic/embeddings.db")

    if not force_refresh and db_path.exists():
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.execute("SELECT vector FROM embeddings WHERE cache_key = ?", (cache_key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        finally:
            conn.close()

    # Calculate vector
    vector = None
    if provider == "openai" and os.environ.get("OPENAI_API_KEY") and not os.environ.get("NOETIC_MOCK_EMBEDDINGS"):
        try:
            import urllib.request
            req_data = json.dumps({"input": text[:8000], "model": model}).encode("utf-8")
            req = urllib.request.Request(
                "https://api.openai.com/v1/embeddings",
                data=req_data,
                headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}", "Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                vector = res_json["data"][0]["embedding"]
        except Exception:
            vector = None

    if vector is None:
        vector = deterministic_vector(text)

    # Store in SQLite cache
    if db_path.parent.exists():
        conn = init_embedding_db(db_path)
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO embeddings (cache_key, vector, provider, model, version, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (cache_key, json.dumps(vector), provider, model, version, datetime.now().isoformat())
                )
        finally:
            conn.close()

    return vector


# Labeled calibration pairs for threshold verification [R1]
CALIBRATION_DATASET = {
    "identical": [
        (
            """Local State: authoritative client replica persisting mutations offline. CRDT Document: conflict-free replicated data structure. When designing persistent client mutations prioritize local persistence over blocking remote rpc because network latency breaks focus. Consistency latency vs storage: recommend local storage sacrifice minimal footprint gain offline usability flip severe disk constraint.""",
            """Local State: authoritative client replica persisting mutations offline. CRDT Document: conflict-free replicated data structure. When designing persistent client mutations prioritize local persistence and local storage over blocking remote rpc because network latency breaks user focus. Consistency latency vs storage: recommend local storage sacrifice minimal footprint gain offline usability flip severe disk constraint."""
        ),
        (
            """Decision Horizon: duration of consequences. When evaluating decision prioritize fast decision for reversible choices over prolonged deliberation because cheap to undo. Speed vs certainty: recommend decide fast on reversible calls sacrifice full certainty gain velocity flip irreversible tattoo consequences.""",
            """Decision Horizon: duration of consequences. When evaluating decision prioritize fast decision for reversible choices over slow deliberation because cheap to undo. Speed vs certainty: recommend fast decision on reversible calls sacrifice full certainty gain velocity flip irreversible tattoo calls."""
        )
    ],
    "cousin": [
        (
            """Decision Reversibility Taxonomy: Classify decisions by reversibility and consequence duration. When evaluating decisions prioritize rapid action on reversible choices over prolonged deliberation because reversible choices are cheap to undo. Speed vs certainty: recommend fast action on reversible choices sacrifice total certainty gain high velocity flip irreversible permanent consequences.""",
            """Decision Reversibility Taxonomy: Classify decisions by reversibility and consequence duration. When evaluating organizational choices prioritize delegating two-way door decisions over executive deliberation because two-way doors are easily reversible. Speed vs executive control: recommend speed on reversible decisions sacrifice management oversight gain organizational velocity flip irreversible one-way door choices."""
        ),
        (
            """Local Replication Architecture: Client-side authoritative database replica storing documents offline. When designing distributed sync prioritize local persistence and conflict resolution over central cloud apis because network partitions are frequent. Latency vs consistency: recommend local availability sacrifice instant global consensus gain offline responsiveness flip financial ledgers.""",
            """Local Replication Architecture: Client-side database replica syncing documents offline with remote servers. When designing distributed applications prioritize background replication and local persistence over direct rest apis because network partitions drop connections. Storage vs simplicity: recommend revision tree storage sacrifice simple schemas gain offline sync capability flip large binary blobs."""
        )
    ],
    "unrelated": [
        (
            """Local State: authoritative client replica persisting mutations offline. CRDT Document: conflict-free replicated data structure. When designing persistent client mutations prioritize local persistence over blocking remote rpc because network latency breaks focus. Consistency latency vs storage: recommend local storage sacrifice minimal footprint gain offline usability flip severe disk constraint.""",
            """Market Gap: mismatch between supply and demand. When looking for market opportunities prioritize cross-domain transfer over inventing from scratch because arbitrage transfers proven mechanisms. Innovation risk vs margin decay: recommend cross-domain transfer sacrifice novelty moat gain proven mechanics flip highly regulated domains."""
        ),
        (
            """Boring Technology: mature battle-tested infrastructure. When choosing production dependencies prioritize standard boring tools over novel unproven frameworks because unknown failure modes exhaust team. Developer excitement vs stability: recommend operational stability sacrifice novelty gain predictable uptime flip core company thesis requires novel tech.""",
            """Decision Horizon: duration of consequences. When evaluating decision prioritize fast decision for reversible choices over prolonged deliberation because cheap to undo. Speed vs certainty: recommend decide fast on reversible calls sacrifice full certainty gain velocity flip irreversible tattoo consequences."""
        )
    ]
}


def calibrate_thresholds(embedding_fn: Callable[[str], list[float]] = deterministic_vector) -> dict:
    """Calibrates similarity thresholds across labeled dataset pairs [R1]."""
    results = {"identical": [], "cousin": [], "unrelated": []}
    for category, pairs in CALIBRATION_DATASET.items():
        for t1, t2 in pairs:
            v1 = embedding_fn(t1)
            v2 = embedding_fn(t2)
            sim = cosine_similarity(v1, v2)
            results[category].append(round(sim, 4))
    return results


def deduplicate_framework(cfg: Config, framework_data: dict) -> dict:
    """Determines whether candidate framework is MERGE, COUSIN, or CREATE [R1, R2].
    
    Tier 1: Slug matching with length/slug guards (avoids false merges on short slugs e.g. "ui", "c4").
    Tier 2: Embedding comparison against existing frameworks.
            Score >= identical threshold -> MERGE
            Score >= cousin threshold -> COUSIN
    Tier 3: Novel -> CREATE
    """
    slug = (framework_data.get("slug") or slugify(framework_data.get("framework_name", ""))).lower().strip()
    
    # Tier 1: Slug matching with length and short-slug guards
    is_guarded_slug = len(slug) < 4 or slug in SHORT_SLUG_GUARDS
    if not is_guarded_slug and cfg.frameworks.is_dir():
        for existing in cfg.frameworks.glob("*.md"):
            if existing.name.lower() in ("readme.md", "index.md"):
                continue
            if existing.stem.lower() == slug or slugify(existing.stem) == slug:
                return {
                    "action": "MERGE",
                    "target_path": existing,
                    "target_slug": existing.stem,
                    "score": 1.0,
                    "reason": f"Tier 1: Exact slug match on '{slug}'",
                }

    # Tier 2: Embedding comparison against existing frameworks in vault
    candidate_text = core_semantic_text(framework_data)
    candidate_vec = get_embedding(candidate_text, cfg)

    best_score = 0.0
    best_target_path: Path | None = None
    best_target_slug: str | None = None

    if cfg.frameworks.is_dir():
        for existing in cfg.frameworks.glob("*.md"):
            if existing.name.lower() in ("readme.md", "index.md"):
                continue
            content = existing.read_text(encoding="utf-8")
            existing_semantic = extract_semantic_text_from_markdown(content)
            if not existing_semantic.strip():
                continue
            existing_vec = get_embedding(existing_semantic, cfg)
            score = cosine_similarity(candidate_vec, existing_vec)
            if score > best_score:
                best_score = score
                best_target_path = existing
                best_target_slug = existing.stem

    identical_threshold = float(cfg.similarity_thresholds.get("identical", 0.85))
    cousin_threshold = float(cfg.similarity_thresholds.get("cousin", 0.65))

    if best_score >= identical_threshold and best_target_path:
        return {
            "action": "MERGE",
            "target_path": best_target_path,
            "target_slug": best_target_slug,
            "score": round(best_score, 4),
            "reason": f"Tier 2: High embedding similarity ({best_score:.3f} >= {identical_threshold:.2f})",
        }

    if best_score >= cousin_threshold and best_target_path:
        return {
            "action": "COUSIN",
            "target_path": best_target_path,
            "target_slug": best_target_slug,
            "score": round(best_score, 4),
            "reason": f"Tier 2: Cousin embedding similarity ({best_score:.3f} >= {cousin_threshold:.2f})",
        }

    # Tier 3: Novel
    return {
        "action": "CREATE",
        "target_path": None,
        "target_slug": None,
        "score": round(best_score, 4),
        "reason": f"Tier 3: Novel framework (best score {best_score:.3f} < {cousin_threshold:.2f})",
    }
