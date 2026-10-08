"""Benchmark matrix: evaluate workflows across CLI harnesses (agy vs claude) and models.

Usage:
    python tools/benchmark_matrix.py [--harnesses agy,claude] [--models gemini-3.8-flash-low,gemini-3.8-flash-high] [--workflows ingest,draft]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from noetic.agents.runners import run_agent, available
from noetic.tools.schema_check import check
from noetic.tools import prompts

# Standard test fixtures for active workflows
WORKFLOW_FIXTURES = {
    "ingest": {
        "schema": "framework",
        "prompt": (
            "Analyze this source text and extract a structured thinking framework:\n\n"
            "SOURCE: 'Steal Like an Artist by Austin Kleon.\n"
            "Core premise: Nothing is completely original. All creative work builds on what came before. "
            "Don't wait until you know who you are to get started; making things is how you discover yourself. "
            "Steal from multiple heroes, never just one, because copying one person is plagiarism, but copying ten is research. "
            "Keep a swipe file of ideas and remix them. Side projects and hobbies are where real breakthroughs occur.'\n\n"
            "Extract the title, core_principles, mental_moves, and anti_patterns into the required schema."
        ),
    },
    "curate": {
        "schema": "curation",
        "prompt": (
            "Evaluate this candidate idea against the taste stances:\n\n"
            "SOURCE: 'A deterministic financial state machine for autonomous debt collection calls.'\n"
            "Extract candidate curation packages, stances, and reasons why it passes or gets rejected."
        ),
    },
    "draft": {
        "schema": "thread",
        "prompt": (
            "Draft a high-density, hook-driven technical Twitter/X thread about why LLMs should interpret user intent "
            "while deterministic backend code authorizes state transitions. Emphasize why direct LLM DB writes fail."
        ),
    },
    "briefing": {
        "schema": "briefing",
        "prompt": (
            "Summarize the morning vault briefing: 3 tasks active (eval benchmark, OTel exporter, MCP tests), "
            "2 blocker risks (Claude API quota 429, LiveKit key rotation), and next 14-day priority."
        ),
    },
}

HARNESS_MODELS = {
    "agy": [
        "gemini-3.8-flash-low",
        "gemini-3.8-flash-high",
        "claude-sonnet-4-6",
        "claude-opus-4-6-thinking",
    ],
    "claude": [
        "sonnet",
        "opus",
    ],
}


def run_benchmark(harnesses: list[str], models_filter: list[str] | None, workflows_filter: list[str] | None) -> list[dict]:
    results = []
    cwd = REPO_ROOT

    target_workflows = [w for w in WORKFLOW_FIXTURES if not workflows_filter or w in workflows_filter]

    print("\n" + "=" * 80)
    print(" NOETIC WORKFLOW BENCHMARK MATRIX (AGY vs CLAUDE)")
    print("=" * 80)

    for harness in harnesses:
        if not available(harness):
            print(f"\n[SKIP] Harness '{harness}' is not available on PATH.")
            continue

        available_models = HARNESS_MODELS.get(harness, [None])
        if models_filter:
            available_models = [m for m in available_models if m in models_filter]

        for model in available_models:
            print(f"\n> Testing Harness: {harness} | Model: {model or 'default'}")
            print("-" * 80)

            for wf_name in target_workflows:
                fixture = WORKFLOW_FIXTURES[wf_name]
                schema_name = fixture["schema"]
                schema = prompts.schema(schema_name)
                prompt = fixture["prompt"]

                print(f"  - Workflow: {wf_name:<10} ... ", end="", flush=True)

                t0 = time.time()
                try:
                    res = run_agent(harness, prompt, schema, cwd=cwd, model=model, timeout=300)
                    duration = round(time.time() - t0, 2)

                    if not res.ok:
                        err_code = res.error.get("code", "ERROR") if res.error else "ERROR"
                        err_detail = res.error.get("detail", "") if res.error else "Failed"
                        print(f"FAILED ({err_code}: {err_detail[:60]}) [{duration}s]")
                        results.append({
                            "harness": harness,
                            "model": model,
                            "workflow": wf_name,
                            "status": err_code,
                            "duration_s": duration,
                            "schema_valid": False,
                            "schema_errors": [err_detail],
                            "cost_usd": res.cost_usd,
                        })
                        continue

                    # Validate schema
                    problems = check(res.data, schema)
                    schema_ok = len(problems) == 0

                    if schema_ok:
                        print(f"PASSED (Schema valid) [{duration}s]")
                    else:
                        print(f"SCHEMA_INVALID ({len(problems)} errors) [{duration}s]")

                    results.append({
                        "harness": harness,
                        "model": model,
                        "workflow": wf_name,
                        "status": "SUCCESS" if schema_ok else "SCHEMA_INVALID",
                        "duration_s": duration,
                        "schema_valid": schema_ok,
                        "schema_errors": problems,
                        "cost_usd": res.cost_usd,
                    })

                except Exception as exc:
                    duration = round(time.time() - t0, 2)
                    print(f"EXCEPTION: {str(exc)[:60]} [{duration}s]")
                    results.append({
                        "harness": harness,
                        "model": model,
                        "workflow": wf_name,
                        "status": "EXCEPTION",
                        "duration_s": duration,
                        "schema_valid": False,
                        "schema_errors": [str(exc)],
                        "cost_usd": None,
                    })

    return results


def print_summary_table(results: list[dict]):
    print("\n" + "=" * 90)
    print(" BENCHMARK RESULTS SUMMARY")
    print("=" * 90)
    header = f"{'Harness':<8} | {'Model':<25} | {'Workflow':<10} | {'Status':<14} | {'Latency':<8} | {'Schema Valid':<12}"
    print(header)
    print("-" * 90)
    for r in results:
        status_str = r["status"]
        valid_str = "YES" if r["schema_valid"] else f"NO ({len(r['schema_errors'])})"
        print(f"{r['harness']:<8} | {str(r['model']):<25} | {r['workflow']:<10} | {status_str:<14} | {r['duration_s']}s{'':<4} | {valid_str:<12}")
    print("=" * 90)


def generate_markdown(results: list[dict]) -> str:
    md = "# Noetic Multi-Harness & Multi-Model Benchmark\n\n"
    md += f"*Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}*\n\n"
    md += "| Harness | Model | Workflow | Status | Latency (s) | Schema Valid | Cost ($) |\n"
    md += "| :--- | :--- | :--- | :--- | :---: | :---: | :---: |\n"
    for r in results:
        valid_str = "✅ Yes" if r["schema_valid"] else f"❌ No ({len(r['schema_errors'])} errs)"
        cost_str = f"${r['cost_usd']:.4f}" if r.get("cost_usd") else "N/A"
        md += f"| `{r['harness']}` | `{r['model']}` | `{r['workflow']}` | `{r['status']}` | {r['duration_s']}s | {valid_str} | {cost_str} |\n"
    return md


def main():
    parser = argparse.ArgumentParser(description="Benchmark workflows across harnesses and models.")
    parser.add_argument("--harnesses", default="agy,claude", help="Comma-separated list of harnesses (agy, claude)")
    parser.add_argument("--models", help="Comma-separated list of model names")
    parser.add_argument("--workflows", help="Comma-separated list of workflows (ingest, curate, draft, briefing)")
    parser.add_argument("--output-json", default="docs/benchmark-matrix.json", help="Path to write JSON output")
    parser.add_argument("--output-md", default="docs/benchmark-matrix.md", help="Path to write Markdown output")
    args = parser.parse_args()

    harnesses = [h.strip() for h in args.harnesses.split(",") if h.strip()]
    models_filter = [m.strip() for m in args.models.split(",")] if args.models else None
    workflows_filter = [w.strip() for w in args.workflows.split(",")] if args.workflows else None

    results = run_benchmark(harnesses, models_filter, workflows_filter)
    print_summary_table(results)

    # Save outputs
    out_json = REPO_ROOT / args.output_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")

    out_md = REPO_ROOT / args.output_md
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(generate_markdown(results), encoding="utf-8")
    print(f"\nSaved reports to {out_json} and {out_md}\n")


if __name__ == "__main__":
    main()
