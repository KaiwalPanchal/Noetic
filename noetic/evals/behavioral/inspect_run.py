import json
from pathlib import Path

res_file = Path(r"C:\External Apps\overmind-taste-engine\noetic\evals\behavioral\results\run-20261109-110530\results.json")
data = json.loads(res_file.read_text(encoding="utf-8"))
results = data["results"]

print("=== SCENARIO SUMMARY ===")
for sc_id, conds in sorted(results.items()):
    status_str = ", ".join(f"{c}: {'PASS' if reps[0].get('passed') else 'FAIL'}" for c, reps in sorted(conds.items()))
    print(f"{sc_id:4s} -> {status_str}")
