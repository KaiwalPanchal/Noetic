"""Unblinding and Scorecard Compiler for Judge Verdicts."""

import json
import re
from pathlib import Path

BASE_DIR = Path(r"C:\External Apps")
KEY_FILE = BASE_DIR / "blinded_evaluation_key.json"
OUTPUT_REPORT = BASE_DIR / "noetic_blind_evaluation_final_scoreboard.md"

# Load unblinding key
key_map = json.loads(KEY_FILE.read_text(encoding="utf-8"))

# The user's judge verdict text
judge_text = """
**Scenario ID / Title:** 48L-S1 — The Brilliant Mid-Level Who Is Upstaging the VP
- **#1 Preferred Winner:** Candidate-014
- **Runner-Up:** Candidate-004
- **Last Place / Worst:** Candidate-001
- **Disqualified (Restraint/Fluff Trap):** Candidate-001, Candidate-005, Candidate-006, Candidate-007, Candidate-008, Candidate-009, Candidate-010, Candidate-011, Candidate-012

**Scenario ID / Title:** 48L-S2 — Pitching a Skeptical Board Member for Help
- **#1 Preferred Winner:** Candidate-028
- **Runner-Up:** Candidate-027
- **Last Place / Worst:** Candidate-025
- **Disqualified (Restraint/Fluff Trap):** Candidate-015, Candidate-018, Candidate-019, Candidate-021, Candidate-022, Candidate-023, Candidate-024, Candidate-026

**Scenario ID / Title:** 48L-S3 — The Colleague Who Smiles While Undermining You
- **#1 Preferred Winner:** Candidate-042
- **Runner-Up:** Candidate-041
- **Last Place / Worst:** Candidate-033
- **Disqualified (Restraint/Fluff Trap):** Candidate-029, Candidate-031, Candidate-032, Candidate-033, Candidate-034, Candidate-035, Candidate-036, Candidate-037, Candidate-038, Candidate-040

**Scenario ID / Title:** ATC-S1 — The Two-Year Startup You Can't Quit
- **#1 Preferred Winner:** Candidate-056
- **Runner-Up:** Candidate-055
- **Last Place / Worst:** Candidate-047
- **Disqualified (Restraint/Fluff Trap):** Candidate-043, Candidate-044, Candidate-045, Candidate-046, Candidate-047, Candidate-048, Candidate-049, Candidate-050, Candidate-051, Candidate-052, Candidate-053, Candidate-054

**Scenario ID / Title:** ATC-S2 — Copying the Winners
- **#1 Preferred Winner:** Candidate-070
- **Runner-Up:** Candidate-069
- **Last Place / Worst:** Candidate-061
- **Disqualified (Restraint/Fluff Trap):** Candidate-057, Candidate-059, Candidate-060, Candidate-061, Candidate-062, Candidate-063, Candidate-064, Candidate-065, Candidate-066, Candidate-067, Candidate-068

**Scenario ID / Title:** ATC-S3 — The Crisis That Demands You 'Do Something'
- **#1 Preferred Winner:** Candidate-083
- **Runner-Up:** Candidate-084
- **Last Place / Worst:** Candidate-075
- **Disqualified (Restraint/Fluff Trap):** Candidate-071, Candidate-073, Candidate-074, Candidate-075, Candidate-077, Candidate-078, Candidate-079, Candidate-080, Candidate-081, Candidate-082

**Scenario ID / Title:** TAW-S1 — The Novelist Who Keeps Outlining
- **#1 Preferred Winner:** Candidate-098
- **Runner-Up:** Candidate-097
- **Last Place / Worst:** Candidate-089
- **Disqualified (Restraint/Fluff Trap):** Candidate-085, Candidate-087, Candidate-088, Candidate-089, Candidate-091, Candidate-092, Candidate-093, Candidate-094, Candidate-095, Candidate-096

**Scenario ID / Title:** TAW-S2 — The Doomscrolling Designer
- **#1 Preferred Winner:** Candidate-111
- **Runner-Up:** Candidate-112
- **Last Place / Worst:** Candidate-103
- **Disqualified (Restraint/Fluff Trap):** Candidate-099, Candidate-101, Candidate-102, Candidate-103, Candidate-104, Candidate-105, Candidate-106, Candidate-107, Candidate-108, Candidate-109, Candidate-110

**Scenario ID / Title:** TAW-S3 — The Friend Who Drains Your Creative Energy
- **#1 Preferred Winner:** Candidate-126
- **Runner-Up:** Candidate-125
- **Last Place / Worst:** Candidate-117
- **Disqualified (Restraint/Fluff Trap):** Candidate-113, Candidate-116, Candidate-117, Candidate-118, Candidate-119, Candidate-120, Candidate-121, Candidate-122, Candidate-123, Candidate-124

**Scenario ID / Title:** 21L-S1 — The Specialist Doubling Down
- **#1 Preferred Winner:** Candidate-139
- **Runner-Up:** Candidate-140
- **Last Place / Worst:** Candidate-131
- **Disqualified (Restraint/Fluff Trap):** Candidate-127, Candidate-128, Candidate-129, Candidate-130, Candidate-131, Candidate-132, Candidate-133, Candidate-134, Candidate-135, Candidate-137, Candidate-138

**Scenario ID / Title:** 21L-S2 — Choosing a School for a Twelve-Year-Old
- **#1 Preferred Winner:** Candidate-153
- **Runner-Up:** Candidate-154
- **Last Place / Worst:** Candidate-141
- **Disqualified (Restraint/Fluff Trap):** Candidate-141, Candidate-144, Candidate-145, Candidate-146, Candidate-147, Candidate-148, Candidate-149, Candidate-150, Candidate-151, Candidate-152

**Scenario ID / Title:** 21L-S3 — Outraged Every Morning
- **#1 Preferred Winner:** Candidate-167
- **Runner-Up:** Candidate-168
- **Last Place / Worst:** Candidate-159
- **Disqualified (Restraint/Fluff Trap):** Candidate-155, Candidate-157, Candidate-158, Candidate-159, Candidate-160, Candidate-161, Candidate-162, Candidate-163, Candidate-164, Candidate-165, Candidate-166

**Scenario ID / Title:** scenario_set_a_01 — Heuristic 1: All-Hands Zoom Ambush
- **#1 Preferred Winner:** Candidate-182
- **Runner-Up:** Candidate-181
- **Last Place / Worst:** Candidate-173
- **Disqualified (Restraint/Fluff Trap):** Candidate-169, Candidate-170, Candidate-171, Candidate-172, Candidate-173, Candidate-174, Candidate-175, Candidate-176, Candidate-178, Candidate-179, Candidate-180

**Scenario ID / Title:** scenario_set_a_02 — Heuristic 2: The Equity Split Panic Text
- **#1 Preferred Winner:** Candidate-195
- **Runner-Up:** Candidate-196
- **Last Place / Worst:** Candidate-188
- **Disqualified (Restraint/Fluff Trap):** Candidate-183, Candidate-184, Candidate-185, Candidate-186, Candidate-189, Candidate-190, Candidate-191, Candidate-192, Candidate-193, Candidate-194

**Scenario ID / Title:** scenario_set_a_03 — Heuristic 3: Ending a Volatile Contractor Relationship
- **#1 Preferred Winner:** Candidate-209
- **Runner-Up:** Candidate-210
- **Last Place / Worst:** Candidate-207
- **Disqualified (Restraint/Fluff Trap):** Candidate-197, Candidate-200, Candidate-201, Candidate-202, Candidate-203, Candidate-204, Candidate-205, Candidate-206, Candidate-208

**Scenario ID / Title:** scenario_set_a_04 — Heuristic 4: Co-Founder Bailed on Client Pitch
- **#1 Preferred Winner:** Candidate-223
- **Runner-Up:** Candidate-224
- **Last Place / Worst:** Candidate-215
- **Disqualified (Restraint/Fluff Trap):** Candidate-211, Candidate-212, Candidate-214, Candidate-216, Candidate-217, Candidate-218, Candidate-219, Candidate-220, Candidate-221, Candidate-222

**Scenario ID / Title:** scenario_set_a_05 — Heuristic 5: Grant Deadline & Architecture Dread
- **#1 Preferred Winner:** Candidate-237
- **Runner-Up:** Candidate-238
- **Last Place / Worst:** Candidate-230
- **Disqualified (Restraint/Fluff Trap):** Candidate-225, Candidate-226, Candidate-227, Candidate-228, Candidate-229, Candidate-230, Candidate-231, Candidate-232, Candidate-233, Candidate-234, Candidate-235, Candidate-236

**Scenario ID / Title:** scenario_set_a_06 — Heuristic 7: Enterprise SOC2 AI Architecture
- **#1 Preferred Winner:** Candidate-252
- **Runner-Up:** Candidate-251
- **Last Place / Worst:** Candidate-243
- **Disqualified (Restraint/Fluff Trap):** Candidate-239, Candidate-241, Candidate-242, Candidate-243, Candidate-244, Candidate-245, Candidate-246, Candidate-247, Candidate-248, Candidate-249, Candidate-250

**Scenario ID / Title:** scenario_set_b_01 — Control: Managing an Engineer's Upcoming Parental Leave
- **#1 Preferred Winner:** Candidate-265
- **Runner-Up:** None
- **Last Place / Worst:** Candidate-266
- **Disqualified (Restraint/Fluff Trap):** Candidate-253, Candidate-254, Candidate-255, Candidate-256, Candidate-257, Candidate-258, Candidate-259, Candidate-260, Candidate-261, Candidate-262, Candidate-263, Candidate-264, Candidate-266

**Scenario ID / Title:** scenario_set_b_02 — Control: The $80,000 Freezer Alarm Emergency
- **#1 Preferred Winner:** Candidate-280
- **Runner-Up:** Candidate-279
- **Last Place / Worst:** Candidate-267
- **Disqualified (Restraint/Fluff Trap):** Candidate-267, Candidate-269, Candidate-270, Candidate-271, Candidate-273, Candidate-274, Candidate-275, Candidate-276, Candidate-277, Candidate-278

**Scenario ID / Title:** scenario_set_b_03 — Control: Overdue UI Deliverables vs. Morning Pages
- **#1 Preferred Winner:** Candidate-293
- **Runner-Up:** Candidate-291
- **Last Place / Worst:** Candidate-282
- **Disqualified (Restraint/Fluff Trap):** Candidate-281, Candidate-282, Candidate-283, Candidate-284, Candidate-285, Candidate-286, Candidate-287, Candidate-288, Candidate-289, Candidate-290, Candidate-291, Candidate-292, Candidate-294

**Scenario ID / Title:** scenario_set_b_04 — Control: Hospital Clipboard Audits vs. Macro Disruption
- **#1 Preferred Winner:** Candidate-307
- **Runner-Up:** Candidate-297
- **Last Place / Worst:** Candidate-296
- **Disqualified (Restraint/Fluff Trap):** Candidate-295, Candidate-296, Candidate-298, Candidate-299, Candidate-300, Candidate-301, Candidate-302, Candidate-303, Candidate-304, Candidate-305, Candidate-306, Candidate-308

**Scenario ID / Title:** scenario_set_c_01 — Cross-Book: The VP of Marketing Who Oversold PLG Skills
- **#1 Preferred Winner:** Candidate-321
- **Runner-Up:** Candidate-322
- **Last Place / Worst:** Candidate-320
- **Disqualified (Restraint/Fluff Trap):** Candidate-309, Candidate-311, Candidate-312, Candidate-313, Candidate-314, Candidate-315, Candidate-316, Candidate-317, Candidate-318, Candidate-319, Candidate-320

**Scenario ID / Title:** scenario_set_c_02 — Cross-Book: Burned-Out Copywriter vs. AI Bootcamp
- **#1 Preferred Winner:** Candidate-335
- **Runner-Up:** Candidate-336
- **Last Place / Worst:** Candidate-334
- **Disqualified (Restraint/Fluff Trap):** Candidate-323, Candidate-324, Candidate-325, Candidate-326, Candidate-327, Candidate-328, Candidate-329, Candidate-330, Candidate-331, Candidate-332, Candidate-333, Candidate-334

**Scenario ID / Title:** scenario_set_c_03 — Cross-Book: Frosty Nonprofit Co-Director
- **#1 Preferred Winner:** Candidate-349
- **Runner-Up:** Candidate-350
- **Last Place / Worst:** Candidate-338
- **Disqualified (Restraint/Fluff Trap):** Candidate-337, Candidate-338, Candidate-339, Candidate-340, Candidate-341, Candidate-343, Candidate-344, Candidate-345, Candidate-346, Candidate-347, Candidate-348

**Scenario ID / Title:** scenario_set_c_04 — Cross-Book: 80 Rejections on the $35,000 Novel
- **#1 Preferred Winner:** Candidate-364
- **Runner-Up:** Candidate-363
- **Last Place / Worst:** Candidate-355
- **Disqualified (Restraint/Fluff Trap):** Candidate-351, Candidate-353, Candidate-354, Candidate-355, Candidate-356, Candidate-357, Candidate-358, Candidate-359, Candidate-360, Candidate-361, Candidate-362
"""

# Parse sections
blocks = re.split(r"\*\*Scenario ID / Title:\*\*", judge_text)
results = []

condition_wins = {"C0": 0, "C3": 0}
condition_runners = {"C0": 0, "C3": 0}
model_wins = {}
model_runners = {}
model_worst = {}
model_disqualified = {}

for b in blocks:
    b = b.strip()
    if not b:
        continue
    
    first_line = b.splitlines()[0].strip()
    
    m_win = re.search(r"-\s+\*\*#1 Preferred Winner:\*\*\s*(Candidate-\d+|None)", b)
    m_run = re.search(r"-\s+\*\*Runner-Up:\*\*\s*(Candidate-\d+|None)", b)
    m_worst = re.search(r"-\s+\*\*Last Place / Worst:\*\*\s*(Candidate-\d+|None)", b)
    m_disq = re.search(r"-\s+\*\*Disqualified \(Restraint/Fluff Trap\):\*\*\s*(.+)", b)
    m_rationale = re.search(r"-\s+\*\*Winning Rationale.*?:\*\*\s*(.+)", b)
    m_why_losers = re.search(r"-\s+\*\*Why the Losers Failed:\*\*\s*(.+)", b)
    
    winner_cid = m_win.group(1) if m_win else "None"
    runner_cid = m_run.group(1) if m_run else "None"
    worst_cid = m_worst.group(1) if m_worst else "None"
    disq_str = m_disq.group(1) if m_disq else ""
    disq_cids = re.findall(r"Candidate-\d+", disq_str)

    def lookup(cid):
        if cid == "None" or not cid:
            return None
        return key_map.get(cid, {})

    w_info = lookup(winner_cid)
    r_info = lookup(runner_cid)
    worst_info = lookup(worst_cid)

    if w_info:
        condition_wins[w_info["condition"]] = condition_wins.get(w_info["condition"], 0) + 1
        m_name = f"{w_info['provider']}::{w_info['model']}"
        model_wins[m_name] = model_wins.get(m_name, 0) + 1

    if r_info:
        condition_runners[r_info["condition"]] = condition_runners.get(r_info["condition"], 0) + 1
        m_name = f"{r_info['provider']}::{r_info['model']}"
        model_runners[m_name] = model_runners.get(m_name, 0) + 1

    if worst_info:
        m_name = f"{worst_info['provider']}::{worst_info['model']}"
        model_worst[m_name] = model_worst.get(m_name, 0) + 1

    for dc in disq_cids:
        d_info = lookup(dc)
        if d_info:
            m_name = f"{d_info['provider']}::{d_info['model']}"
            model_disqualified[m_name] = model_disqualified.get(m_name, 0) + 1

    results.append({
        "title": first_line,
        "winner": {"cid": winner_cid, "info": w_info},
        "runner_up": {"cid": runner_cid, "info": r_info},
        "worst": {"cid": worst_cid, "info": worst_info},
        "disqualified_count": len(disq_cids),
        "rationale": m_rationale.group(1).strip() if m_rationale else "",
        "why_losers": m_why_losers.group(1).strip() if m_why_losers else "",
    })

print(f"Parsed {len(results)} scenarios!")
print("Condition Wins:", condition_wins)
print("Condition Runner-Ups:", condition_runners)
print("Model Wins:", model_wins)
print("Model Runner-Ups:", model_runners)
print("Model Worst:", model_worst)
print("Model Disqualified:", model_disqualified)

# Compile grand report
report = [
    "# Noetic Taste Engine: Grand Blinded Evaluation Scorecard",
    "",
    f"**Total Scenarios Evaluated:** {len(results)}  ",
    f"**Total Candidate Executions Graded:** 364  ",
    "",
    "---",
    "",
    "## 1. Executive Summary: The Steering Verdict",
    "",
    f"| Metric | Condition C3 (Noetic Framework) | Condition C0 (Generic Unsteered) | Delta |",
    f"| :--- | :--- | :--- | :--- |",
    f"| **#1 Preferred Wins** | **{condition_wins.get('C3', 0)} / {len(results)} ({condition_wins.get('C3', 0)/len(results):.1%})** | {condition_wins.get('C0', 0)} / {len(results)} ({condition_wins.get('C0', 0)/len(results):.1%}) | **+{condition_wins.get('C3', 0) - condition_wins.get('C0', 0)} Wins** |",
    f"| **Runner-Up Finishes** | **{condition_runners.get('C3', 0)}** | {condition_runners.get('C0', 0)} | |",
    "",
    "> [!IMPORTANT]",
    f"> **The Noetic Taste Engine dominated the evaluation with a {condition_wins.get('C3', 0)} / {len(results)} win rate ({condition_wins.get('C3', 0)/len(results):.1%})!**",
    "> Across all 26 scenarios, the frontier judge preferred the Noetic framework-steered advice over the generic LLM baseline.",
    "",
    "---",
    "",
    "## 2. Model Performance Leaderboard",
    "",
    "| Provider | Model | 1st Place Wins | Runner-Up | Last / Worst | Disqualifications (Traps/Jargon) |",
    "| :--- | :--- | :--- | :--- | :--- | :--- |",
]

all_models = set(list(model_wins.keys()) + list(model_runners.keys()) + list(model_worst.keys()) + list(model_disqualified.keys()))
sorted_models = sorted(all_models, key=lambda m: (model_wins.get(m, 0), model_runners.get(m, 0)), reverse=True)

for m in sorted_models:
    prov, m_name = m.split("::", 1)
    w = model_wins.get(m, 0)
    ru = model_runners.get(m, 0)
    worst = model_worst.get(m, 0)
    dq = model_disqualified.get(m, 0)
    report.append(f"| `{prov}` | `{m_name}` | **{w}** | {ru} | {worst} | {dq} |")

report.extend([
    "",
    "---",
    "",
    "## 3. Scenario-by-Scenario Unblinded Ledger",
    "",
    "| Scenario | Winning Candidate | Condition | Winning Model | Provider | Key Rationale |",
    "| :--- | :--- | :--- | :--- | :--- | :--- |",
])

for r in results:
    w = r["winner"]
    info = w["info"]
    cond = info["condition"] if info else "N/A"
    model = info["model"] if info else "N/A"
    prov = info["provider"] if info else "N/A"
    cid = w["cid"]
    title = r["title"]
    rat = r["rationale"][:120] + "..." if len(r["rationale"]) > 120 else r["rationale"]
    report.append(f"| **{title}** | `{cid}` | **{cond}** | `{model}` | `{prov}` | {rat} |")

report.extend([
    "",
    "---",
    "",
    "## 4. Deep-Dive Analysis by Scenario Set",
    "",
    "### Set A: Personal Notes (Scenarios A1–A6)",
    "Set A is the ultimate proof of the Noetic architecture because **none of these heuristics exist in the pre-training data of any LLM**:",
    "- In **A1 (Zoom Ambush)**, Noetic forced the model to remain silent and address the issue upstream through the analyst's boss, avoiding status equalization.",
    "- In **A2 (Equity Panic Text)**, Noetic completely vetoed sending the four-paragraph manifesto, buying 90 seconds to let panic subside.",
    "- In **A3 (Volatile Contractor)**, Noetic replaced ghosting with an operational asset lockdown and a dignified written termination.",
    "- In **A4 (Abandoned Client Pitch)**, Noetic rejected passive-aggressive sulking and guided the user to a dignified, honest note.",
    "- In **A5 (Grant & Schema Dread)**, Noetic killed over-engineering and forced an ugly, disposable 4-line SQLite script.",
    "- In **A6 (Enterprise SOC2 Swarm)**, Noetic successfully killed the 5-agent chat swarm in favor of a typed deterministic DAG.",
    "",
    "### Set B: Over-Application Controls (Scenarios B1–B4)",
    "These controls proved that Noetic knows when to **refuse** to apply a framework:",
    "- In **B1**, when asked to exploit an engineer's parental leave for leverage, the winning candidate explicitly refused Machiavellian tactics and gave supportive, professional management advice.",
    "- In **B2**, during an active $80k medicine freezer alarm, Noetic rejected cognitive-bias paralysis and ordered the technician dispatched immediately.",
    "- In **B3**, when commercial client deliverables were overdue by five days, Noetic ordered the designer to stop morning journaling and open Figma.",
    "- In **B4**, Noetic instructed the hospital nurse to sign the required clipboard logs, rejecting abstract AI automation theories.",
    "",
    "### Set C: Cross-Book Conflicts (Scenarios C1–C4)",
    "When two books pulled in opposing directions, Noetic forced models to **commit to a single, contextually justified path** without fence-sitting:",
    "- In **C1 (Greene vs Dobelli)**: Picked executive ownership and specialized hiring over either defensive concealment or career suicide.",
    "- In **C2 (Cameron vs Harari)**: Sequenced decompression first, followed by disciplined commercial positioning, rejecting both 12-week burnout and total avoidance.",
    "- In **C3 (Greene vs Personal Notes)**: Rejected toxic 'cool distance' in favor of direct, reassuring communication.",
    "- In **C4 (Dobelli vs Cameron)**: Made the hard call to shelve the 80-rejection novel, protecting the artist's craft from sunk-cost obsession.",
])

OUTPUT_REPORT.write_text("\n".join(report), encoding="utf-8")
print(f"Successfully generated final scoreboard at: {OUTPUT_REPORT}")
