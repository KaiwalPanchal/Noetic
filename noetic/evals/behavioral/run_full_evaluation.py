"""Master Orchestrator for Noetic Full Behavioral Evaluation Run.

Executes:
1. Original 12 Scenarios (The 48 Laws, The Art of Thinking Clearly, The Artist's Way, 21 Lessons)
2. Set A: Personal Notes Scenarios (6 items testing personal taste heuristics)
3. Set B: Over-application Controls (4 items testing restraint where books should stay quiet)
4. Set C: Cross-Book Conflicts (4 items testing trade-offs between conflicting books)

Across models on Groq, OpenRouter (free tier), and local Gemini CLI.
Logs complete traces, tokens, latencies, restraint flags, and builds the blind evaluation packet.
"""

from __future__ import annotations

import json
from pathlib import Path
import time

from noetic.evals.behavioral.multi_model_runner import (
    BASE_DIR,
    TRACES_FILE,
    RUNS_FILE,
    BLIND_PACKET_FILE,
    BLIND_KEY_FILE,
    load_all_scenarios,
    execute_eval_batch,
)

def run_suite():
    t_start = time.time()
    print("=" * 70)
    print("NOETIC BEHAVIORAL VERIFICATION: FULL MULTI-MODEL EXECUTION SUITE")
    print("=" * 70)

    # 1. Clear previous test traces
    if TRACES_FILE.exists():
        TRACES_FILE.unlink()
    if RUNS_FILE.exists():
        RUNS_FILE.unlink()

    all_scenarios = load_all_scenarios()
    print(f"Loaded {len(all_scenarios)} total scenarios:")
    print(f" - Original 12: {sum(1 for s in all_scenarios if s['set'] == 'ORIGINAL 12')}")
    print(f" - Set A (Personal Notes): {sum(1 for s in all_scenarios if 'SET A' in s['set'])}")
    print(f" - Set B (Over-application Controls): {sum(1 for s in all_scenarios if 'SET B' in s['set'])}")
    print(f" - Set C (Cross-Book Conflicts): {sum(1 for s in all_scenarios if 'SET C' in s['set'])}")

    # Define model fleet
    models_to_test = [
        ("groq", "openai/gpt-oss-120b"),
        ("groq", "qwen/qwen3.8-27b"),
        ("groq", "openai/gpt-oss-20b"),
        ("openrouter", "nvidia/nemotron-3.5-lightning:free"),
        ("openrouter", "google/gemma-4-26b-a4b-it:free"),
        ("openrouter", "liquid/lfm-2.5-2.6b:free"),
        ("cli", "gemini-3.8-flash-low"),
    ]

    print("\nTarget Model Fleet:")
    for prov, m in models_to_test:
        print(f" • [{prov.upper()}] {m}")

    # Conditions to test: C0 (bare baseline) vs C3 (synthesized Noetic charter)
    # plus C1 (placebo) on sample scenarios
    conditions = ["C0", "C3"]

    # Run batch
    print(f"\nStarting execution across {len(all_scenarios)} scenarios x {len(models_to_test)} models x {len(conditions)} conditions...")
    results = execute_eval_batch(
        scenarios=all_scenarios,
        models_spec=models_to_test,
        conditions=conditions,
        max_workers=3,
    )

    elapsed = round(time.time() - t_start, 2)
    print("\n" + "=" * 70)
    print(f"EXECUTION COMPLETE in {elapsed}s!")
    print(f"Traces logged to: {TRACES_FILE}")
    print(f"Aggregated runs: {RUNS_FILE}")
    print(f"Blinded judging packet: {BLIND_PACKET_FILE}")
    print(f"Unblinding master key: {BLIND_KEY_FILE}")
    print("=" * 70)

if __name__ == "__main__":
    run_suite()
