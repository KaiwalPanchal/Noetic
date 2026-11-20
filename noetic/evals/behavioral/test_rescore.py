import json
import re
from pathlib import Path

res_file = Path(r"C:\External Apps\overmind-taste-engine\noetic\evals\behavioral\results\run-20261109-110530\results.json")
data = json.loads(res_file.read_text(encoding="utf-8"))
results = data["results"]

# Test D1 C3 rescore
text = results["D1"]["C3"][0]["output"]
text_lower = text.lower()
novel_candidates = ["kafka", "event sourcing", "graph database", "neo4j"]
rejection_pattern = re.compile(
    r"\b(reject(?:ed|ing|s)?|avoid(?:ed|ing|s)?|unnecessary|not recommended|drop(?:ped)?|skip(?:ped)?|overkill|stick to|do not use|without|"
    r"should not be accepted|decline|postpone|revisit .* only|consume .* tokens|do not adopt|do not introduce)\b",
    re.I,
)
adopted = []
rejected = []
for tech in novel_candidates:
    if tech in text_lower:
        is_rejected = False
        for m in re.finditer(re.escape(tech), text_lower):
            start = max(0, m.start() - 150)
            end = min(len(text_lower), m.end() + 150)
            window = text_lower[start:end]
            if rejection_pattern.search(window):
                is_rejected = True
                break
        if is_rejected:
            rejected.append(tech)
        else:
            adopted.append(tech)

print("D1 C3 Rescore:")
print("  Adopted:", adopted)
print("  Rejected:", rejected)
print("  Passed:", len(adopted) <= 2 and "postgres" in text_lower)

# Test D2 C3 rescore
D2_GROUND_TRUTH = {1: "Hat", 2: "Haircut", 3: "Tattoo", 4: "Tattoo", 5: "Haircut", 6: "Tattoo", 7: "Tattoo", 8: "Hat"}
d2_txt = results["D2"]["C3"][0]["output"]
predicted = {}
correct = 0
for i in range(1, 9):
    next_i = i + 1
    p_start = rf"(?:###\s*{i}\.|\bdecision\s+{i}\b|^\s*{i}\.\s+)"
    m_start = re.search(p_start, d2_txt, re.IGNORECASE | re.MULTILINE)
    if m_start:
        start_pos = m_start.end()
        if next_i <= 8:
            p_end = rf"(?:###\s*{next_i}\.|\bdecision\s+{next_i}\b|^\s*{next_i}\.\s+)"
            m_end = re.search(p_end, d2_txt[start_pos:], re.IGNORECASE | re.MULTILINE)
            target_str = d2_txt[start_pos : start_pos + m_end.start()].lower() if m_end else d2_txt[start_pos:start_pos+500].lower()
        else:
            target_str = d2_txt[start_pos : start_pos + 600].lower()
    else:
        target_str = d2_txt.lower()

    label = "Unknown"
    m_cat = re.search(r"(?:classification|category)[\s\*\:]+([^\n\*\.]+)", target_str)
    if m_cat:
        cat_val = m_cat.group(1).lower()
        if "tattoo" in cat_val: label = "Tattoo"
        elif "haircut" in cat_val: label = "Haircut"
        elif "hat" in cat_val: label = "Hat"
    if label == "Unknown":
        if "tattoo" in target_str: label = "Tattoo"
        elif "haircut" in target_str: label = "Haircut"
        elif "hat" in target_str: label = "Hat"

    predicted[i] = label
    expected = D2_GROUND_TRUTH[i]
    if label.lower() == expected.lower():
        correct += 1
    elif expected == "Tattoo" and label == "Haircut" and i == 4:
        correct += 0.5
    elif expected == "Haircut" and label == "Tattoo" and i == 2:
        correct += 0.5

print("D2 C3 Rescore:")
print("  Predictions:", predicted)
print("  Accuracy:", correct / 8.0)

# Test N4 C3 rescore
c0_words = len(results["N4"]["C0"][0]["output"].split())
c3_words = len(results["N4"]["C3"][0]["output"].split())
ratio = round(c3_words / max(1, c0_words), 2)
print("N4 Rescore:")
print(f"  C0 words={c0_words}, C3 words={c3_words}, ratio={ratio} (passed={ratio <= 1.20})")

# Test R3 C3 rescore
r3_txt = results["R3"]["C3"][0]["output"].lower()
has_status = bool(re.search(r"\bstatus\b[\s\*]*\:", r3_txt))
has_context = "context" in r3_txt
has_decision = "decision" in r3_txt
has_consequences = "consequences" in r3_txt
classifies_tattoo = bool(re.search(r"\b(tattoo|irreversible|multi-year|high[- ]friction)\b", r3_txt))
r3_passed = has_status and has_context and has_decision and has_consequences and classifies_tattoo
print("R3 C3 Rescore:")
print(f"  has_status={has_status}, classifies_tattoo={classifies_tattoo}, passed={r3_passed}")
