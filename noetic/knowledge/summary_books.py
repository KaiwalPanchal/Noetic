import json
from pathlib import Path

FRAMEWORKS_DIR = Path(r"C:\External Apps\overmind-taste-engine\noetic\evals\behavioral\vault_fixture\frameworks")

for key in ["48-laws-of-power", "art-of-thinking-clearly", "the-artists-way", "21-lessons-for-21st-century"]:
    data = json.loads((FRAMEWORKS_DIR / f"{key}.json").read_text(encoding="utf-8"))
    title = data.get("framework_name")
    domain = data.get("ontology", {}).get("domain")
    core_idea = data.get("core_idea")
    print(f"\n{'='*75}")
    print(f"📖 {title} [{domain}]")
    print(f"{'='*75}")
    print(f"Core Worldview:\n  {core_idea}\n")
    print("Top Directional Heuristics:")
    for i, h in enumerate(data.get("directional_heuristics", [])[:3], 1):
        ctx = h.get("context") or h.get("when", "")
        p = h.get("prioritize", "")
        o = h.get("over", "")
        b = h.get("because", "")
        print(f"  {i}. When: {ctx}")
        print(f"     Prioritize: {p}")
        print(f"     Over:       {o}")
        print(f"     Because:    {b}\n")
