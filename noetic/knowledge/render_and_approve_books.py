"""Render canonical markdown notes and approve all 4 compiled book frameworks."""

import json
from pathlib import Path
from datetime import datetime, timezone

from noetic.knowledge.config import Config
from noetic.knowledge.notes import framework as write_framework_note
from noetic.gates.gate import approve, verify_approval_hash

VAULT_DIR = Path(r"C:\External Apps\overmind-taste-engine\noetic\evals\behavioral\vault_fixture")
FRAMEWORKS_DIR = VAULT_DIR / "frameworks"

cfg = Config(VAULT_DIR, json.loads((VAULT_DIR / "noetic.config.json").read_text(encoding="utf-8")))
run_id = f"book-compile-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

keys = [
    "48-laws-of-power",
    "art-of-thinking-clearly",
    "the-artists-way",
    "21-lessons-for-21st-century",
]

for key in keys:
    json_path = FRAMEWORKS_DIR / f"{key}.json"
    if not json_path.exists():
        print(f"Missing {json_path}")
        continue
    
    fw_data = json.loads(json_path.read_text(encoding="utf-8"))
    fw_data["slug"] = key
    
    # Ensure directional_heuristics have context and operational_rule
    for h in fw_data.get("directional_heuristics", []):
        if "context" not in h:
            h["context"] = h.get("when", "applicable situations")
        if "operational_rule" not in h:
            h["operational_rule"] = h.get("prioritize", "")
        if "tier" not in h:
            h["tier"] = 2
            
    note_path = write_framework_note(cfg, fw_data, agent="book-compiler", run_id=run_id)
    approve(note_path, note=f"Approved compiled framework: {fw_data.get('framework_name')}")
    is_valid = verify_approval_hash(note_path)
    print(f"✓ {note_path.name}: Written, approved, hash_valid={is_valid}")
