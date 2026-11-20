import inspect
import json
from pathlib import Path
from noetic.knowledge.notes import append_application

print("append_application signature:", inspect.signature(append_application))

res_file = Path(r"C:\External Apps\overmind-taste-engine\noetic\evals\behavioral\results\run-20261109-110530\results.json")
data = json.loads(res_file.read_text(encoding="utf-8"))
results = data["results"]

print("\n--- D1 [C3] ---")
print("scores:", results["D1"]["C3"][0].get("scores"))
print("output head:\n", results["D1"]["C3"][0]["output"][:400])

print("\n--- N4 [C3] ---")
print("scores:", results["N4"]["C3"][0].get("scores"))
print("output:\n", results["N4"]["C3"][0]["output"])

print("\n--- R3 [C3] ---")
print("scores:", results["R3"]["C3"][0].get("scores"))
print("output head:\n", results["R3"]["C3"][0]["output"][:400])
