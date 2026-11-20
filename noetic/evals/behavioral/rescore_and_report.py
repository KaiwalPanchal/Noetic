"""Re-scores behavioral verification results and compiles final report."""

import json
from pathlib import Path
from datetime import datetime, timezone

from noetic.evals.behavioral.scorers.det_scorers import (
    score_d1_tech_count,
    score_d4_interface_depth,
    score_d5_canary_ledger,
    score_n4_overhead,
    score_s1_collision_charter,
    score_s2_tier_hierarchy,
    score_x1_security_mcp_trust,
)
from noetic.evals.behavioral.scorers.gt_scorers import (
    score_d2_classification,
    score_r1_seeded_flaws,
    score_r2_pr_review,
    score_r3_adr,
)
from noetic.evals.behavioral.scorers.rubric_judges import (
    judge_d1_reasoning,
    judge_d3_local_first,
    judge_n1_css_restraint,
    judge_n2_override,
    judge_n3_user_mandate,
    judge_s3_scaled_stacking,
)
from noetic.evals.behavioral.stage1_fidelity import run_stage1_fidelity_check
from noetic.evals.behavioral.report_generator import compute_metrics, generate_markdown_report
from noetic.knowledge.notes import append_application, verify_approval_hash

RESULTS_FILE = Path(r"C:\External Apps\overmind-taste-engine\noetic\evals\behavioral\results\run-20261109-110530\results.json")
VAULT_DIR = Path(r"C:\External Apps\overmind-taste-engine\noetic\evals\behavioral\vault_fixture")

data = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
results = data["results"]

print("Re-evaluating scorers across all 68 runs...")

# Re-score D1
for cond, reps in results.get("D1", {}).items():
    for r in reps:
        out = r["output"]
        det = score_d1_tech_count(out)
        judge = judge_d1_reasoning(out)
        r["scores"] = {"det": det, "judge": judge}
        r["passed"] = det["passed"] and judge["passed"]

# Re-score D2
for cond, reps in results.get("D2", {}).items():
    for r in reps:
        out = r["output"]
        gt = score_d2_classification(out)
        r["scores"] = {"gt": gt}
        r["passed"] = gt["passed"]

# Re-score N4 (using actual C0 run text as baseline)
c0_text = results.get("N4", {}).get("C0", [{}])[0].get("output", "")
for cond, reps in results.get("N4", {}).items():
    for r in reps:
        out = r["output"]
        det = score_n4_overhead(out, c0_text)
        r["scores"] = {"det": det}
        r["passed"] = det["passed"]

# Re-score R3
for cond, reps in results.get("R3", {}).items():
    for r in reps:
        out = r["output"]
        gt = score_r3_adr(out)
        r["scores"] = {"gt": gt}
        r["passed"] = gt["passed"]

# Save updated results.json
RESULTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Updated results saved to {RESULTS_FILE}")

# Update Applications Log on vault_fixture frameworks
append_application(VAULT_DIR / "frameworks" / "boring-technology.md", kind="eval", artifact_ref="D1-inventory-stack", outcome="followed")
append_application(VAULT_DIR / "frameworks" / "canary-ledger.md", kind="eval", artifact_ref="D5-order-handler", outcome="followed")
append_application(VAULT_DIR / "frameworks" / "hats-haircuts-tattoos.md", kind="eval", artifact_ref="D2-reversibility", outcome="followed")

print("Checking cryptographic approval hashes after application logging:")
for fw in ["boring-technology.md", "canary-ledger.md", "hats-haircuts-tattoos.md"]:
    ok = verify_approval_hash(VAULT_DIR / "frameworks" / fw)
    print(f"  {fw}: hash valid = {ok}")

# Compute metrics and generate report
stage1_res = run_stage1_fidelity_check()
metrics = compute_metrics(data, stage1_res)
report_doc = generate_markdown_report(data, metrics, stage1_res)

print("Report generation complete!")
