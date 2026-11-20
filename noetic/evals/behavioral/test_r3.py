import json
import re
from pathlib import Path

res_file = Path(r"C:\External Apps\overmind-taste-engine\noetic\evals\behavioral\results\run-20261109-110530\results.json")
data = json.loads(res_file.read_text(encoding="utf-8"))

adr_c3 = data["results"]["R3"]["C3"][0]["output"].lower()
print("R3 C3 has status regex:", bool(re.search(r"\bstatus\b[\s\*]*\:", adr_c3)))
print("R3 C3 has context:", "context" in adr_c3)
print("R3 C3 has decision:", "decision" in adr_c3)
print("R3 C3 has consequences:", "consequences" in adr_c3)
print("R3 C3 classifies tattoo:", bool(re.search(r"\b(tattoo|irreversible|multi-year|high[- ]friction)\b", adr_c3)))
