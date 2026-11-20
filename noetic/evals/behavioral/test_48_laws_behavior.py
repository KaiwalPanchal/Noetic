"""Run live behavioral comparison: Generic AI (C0) vs 48 Laws of Power (C3)."""

from noetic.evals.behavioral.runner import call_agent_raw
from noetic.knowledge.config import Config
from noetic.knowledge.stack import stack_frameworks_logic
from pathlib import Path
import json

VAULT_DIR = Path(r"C:\External Apps\overmind-taste-engine\noetic\evals\behavioral\vault_fixture")
cfg = Config(VAULT_DIR, json.loads((VAULT_DIR / "noetic.config.json").read_text(encoding="utf-8")))

prompt = (
    "I am a talented senior engineer at a growing firm. In yesterday's all-hands architecture review, "
    "the VP of Engineering presented a flawed technical roadmap. I spoke up, took over the whiteboard, "
    "publicly dissected his mathematical errors, and showed the whole engineering department my superior alternative design. "
    "The engineering team cheered for me, but today the VP seems cold, excluded me from the leadership dinner, "
    "and reassigned my marquee project to a junior colleague. "
    "How should I evaluate what happened, and what exact strategy should I follow to recover my standing?"
)

# 1. Condition C0: Bare model prompt
prompt_c0 = f"You are an expert career and executive advisor. Answer this request directly:\n\n{prompt}"
print("Executing Condition C0 (Generic AI)...")
output_c0 = call_agent_raw(prompt_c0)

# 2. Condition C3: Stacked with The 48 Laws of Power
charter = stack_frameworks_logic(cfg, slugs=["48-laws-of-power"], task=prompt)
charter_str = json.dumps(charter, indent=2)

prompt_c3 = (
    f"### Architectural Guidance (Active Framework: The 48 Laws of Power)\n"
    f"{charter_str}\n\n"
    f"### User Situation\n{prompt}"
)
print("Executing Condition C3 (48 Laws of Power Framework)...")
output_c3 = call_agent_raw(prompt_c3)

res = {
    "prompt": prompt,
    "c0_generic": output_c0,
    "c3_framework": output_c3,
}

out_file = Path(r"C:\External Apps\48_laws_comparison.json")
out_file.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n✓ Comparison complete! Saved to {out_file}")

print("\n=== GENERIC AI (C0) SNIPPET ===")
print(output_c0[:400])

print("\n=== 48 LAWS AI (C3) SNIPPET ===")
print(output_c3[:400])
