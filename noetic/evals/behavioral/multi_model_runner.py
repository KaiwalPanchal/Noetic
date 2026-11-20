"""Multi-Model and Multi-Condition Behavioral Evaluation Runner for Noetic.

Executes scenarios across Groq, OpenRouter (free tier), and local Gemini CLI.
Logs full traces, token usage, latency, restraint violations, and builds blinded evaluation files.
"""

from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import re
import subprocess
import time
from typing import Any
import urllib.error
import urllib.request
import uuid

from noetic.knowledge.config import Config
from noetic.knowledge.stack import stack_frameworks_logic, parse_framework_note

# Directory paths
BASE_DIR = Path(r"C:\External Apps")
ENGINE_DIR = BASE_DIR / "overmind-taste-engine"
BEHAVIORAL_DIR = ENGINE_DIR / "noetic" / "evals" / "behavioral"
VAULT_DIR = BEHAVIORAL_DIR / "vault_fixture"
FW_DIR = VAULT_DIR / "frameworks"
TRACES_FILE = BASE_DIR / "noetic_eval_traces.jsonl"
RUNS_FILE = BASE_DIR / "noetic_eval_runs.json"
BLIND_PACKET_FILE = BASE_DIR / "blinded_evaluation_packet.md"
BLIND_KEY_FILE = BASE_DIR / "blinded_evaluation_key.json"

# Load API keys from .env
env_file = BASE_DIR / ".env"
ENV: dict[str, str] = {}
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            ENV[k] = v

GROQ_KEY = ENV.get("GROQ_API_KEY", "")
OPENROUTER_KEY = ENV.get("OPENROUTER_API_KEY", "")

cfg = Config(VAULT_DIR, json.loads((VAULT_DIR / "noetic.config.json").read_text(encoding="utf-8")))

# Define target models
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "allam-2-7b",
]

OPENROUTER_MODELS = [
    "nvidia/nemotron-3.5-lightning:free",
    "google/gemma-4-26b-a4b-it:free",
    "liquid/lfm-2.5-2.6b:free",
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "recursive/flint-v1.0:free",
]

CLI_MODELS = [
    "gemini-3.8-flash-low",
]


def call_groq_api(model: str, prompt: str, timeout: int = 45) -> dict[str, Any]:
    """Calls Groq Chat Completions API with usage telemetry."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "NoeticEval/1.0",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
        "max_tokens": 1200,
    }
    data = json.dumps(payload).encode("utf-8")
    t0 = time.time()
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                lat = round(time.time() - t0, 3)
                res = json.loads(resp.read().decode("utf-8"))
                choice = res["choices"][0]
                usage = res.get("usage", {})
                return {
                    "success": True,
                    "output": choice["message"]["content"].strip(),
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "latency_s": lat,
                    "finish_reason": choice.get("finish_reason", "stop"),
                }
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(2.0 * (attempt + 1))
                continue
            err_body = e.read().decode("utf-8", errors="replace")
            return {
                "success": False,
                "output": f"HTTP_ERROR_{e.code}: {err_body}",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "latency_s": round(time.time() - t0, 3),
                "finish_reason": "error",
            }
        except Exception as e:
            if attempt < 2:
                time.sleep(1.5)
                continue
            return {
                "success": False,
                "output": f"EXCEPTION: {e}",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "latency_s": round(time.time() - t0, 3),
                "finish_reason": "error",
            }
    return {"success": False, "output": "TIMEOUT", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "latency_s": round(time.time() - t0, 3), "finish_reason": "timeout"}


def call_openrouter_api(model: str, prompt: str, timeout: int = 60) -> dict[str, Any]:
    """Calls OpenRouter Free Tier API with automatic rate-limit backoff."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-Title": "NoeticEval",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
        "max_tokens": 1200,
    }
    data = json.dumps(payload).encode("utf-8")
    t0 = time.time()
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                lat = round(time.time() - t0, 3)
                res = json.loads(resp.read().decode("utf-8"))
                choice = res["choices"][0]
                usage = res.get("usage", {})
                return {
                    "success": True,
                    "output": choice["message"]["content"].strip(),
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "latency_s": lat,
                    "finish_reason": choice.get("finish_reason", "stop"),
                }
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                wait_time = 3.0 * (attempt + 1)
                time.sleep(wait_time)
                continue
            err_body = e.read().decode("utf-8", errors="replace")
            return {
                "success": False,
                "output": f"HTTP_ERROR_{e.code}: {err_body}",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "latency_s": round(time.time() - t0, 3),
                "finish_reason": "error",
            }
        except Exception as e:
            if attempt < 3:
                time.sleep(2.0)
                continue
            return {
                "success": False,
                "output": f"EXCEPTION: {e}",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "latency_s": round(time.time() - t0, 3),
                "finish_reason": "error",
            }
    return {"success": False, "output": "TIMEOUT", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "latency_s": round(time.time() - t0, 3), "finish_reason": "timeout"}


def call_cli_agent(model: str, prompt: str, timeout: int = 120) -> dict[str, Any]:
    """Calls local agy CLI with latency measurement."""
    tmp_dir = BEHAVIORAL_DIR / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    stamp = f"{int(time.time() * 1000)}_{os.getpid()}_{random.randint(1000, 9999)}"
    prompt_file = tmp_dir / f"runner-prompt-{stamp}.md"
    prompt_file.write_text(prompt, encoding="utf-8")

    short_prompt = f"Read the file {prompt_file} in full. It contains your complete task instructions and context. Follow them exactly and output your response directly."
    cmd = [
        "cmd.exe", "/c", "agy", "-p", short_prompt,
        "--model", model,
        "--disable-slash-commands",
    ]
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        lat = round(time.time() - t0, 3)
        out = proc.stdout.strip()
        words = len(out.split())
        est_tokens = int(words * 1.33)
        return {
            "success": True,
            "output": out,
            "prompt_tokens": int(len(prompt.split()) * 1.33),
            "completion_tokens": est_tokens,
            "total_tokens": int(len(prompt.split()) * 1.33) + est_tokens,
            "latency_s": lat,
            "finish_reason": "stop",
        }
    except Exception as e:
        return {
            "success": False,
            "output": f"EXCEPTION: {e}",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "latency_s": round(time.time() - t0, 3),
            "finish_reason": "error",
        }
    finally:
        prompt_file.unlink(missing_ok=True)


def check_global_restraint(text: str, banned_terms: list[str]) -> dict[str, Any]:
    """Evaluates whether the response complies with the Global Restraint Rule."""
    text_lower = text.lower()
    violations = []

    # 1. Banned terms
    for b in banned_terms:
        if b.lower() in text_lower:
            violations.append(f"banned_term: '{b}'")

    # 2. Book report phrasing
    if re.search(r"\b(according to the book|as .* writes in|in his book|in the chapter|in chapter \d+)\b", text_lower):
        violations.append("book-report phrasing")

    # 3. Bold concept headers
    header_matches = re.findall(r"^#{1,4}\s+.*(?:Bias|Illusion|Fallacy|Censor|Pages|Law\s+\d+|Effect|Heuristic)", text, re.MULTILINE | re.IGNORECASE)
    if header_matches:
        violations.extend([f"bold_concept_header: '{h.strip()}'" for h in header_matches])

    # 4. Explicit label names of biases, techniques, or laws
    bias_labels = [
        "action bias", "survivorship bias", "swimmer's body illusion", "sunk cost fallacy",
        "morning pages", "the censor", "artist date", "crazymakers", "shadow artists",
        "illusion of control", "forecast illusion", "endowment effect", "outcome bias",
        "clustering illusion", "social proof", "law 1", "law 3", "law 4", "law 9", "law 13", "law 14", "law 19", "law 30", "law 35", "law 46"
    ]
    for lbl in bias_labels:
        if re.search(rf"\b{re.escape(lbl)}\b", text_lower):
            violations.append(f"technique_label: '{lbl}'")

    # 5. Canonical book parables
    canonical_examples = [
        "bullet holes on returning bombers", "abraham wald",
        "swimmers have that body because", "swimmers' body",
        "fountain pen on cheap paper", "three pages longhand"
    ]
    for ce in canonical_examples:
        if ce in text_lower:
            violations.append(f"canonical_example: '{ce}'")

    return {
        "restraint_passed": len(violations) == 0,
        "violations": violations,
    }


def build_condition_prompt(scenario: dict, condition: str) -> tuple[str, list[str]]:
    """Builds prompt for condition C0, C1, C2, C3 and returns (assembled_prompt, framework_slugs)."""
    p = scenario["prompt"]
    slugs = scenario.get("slugs", [])

    if condition == "C0":
        # Bare unsteered baseline
        assembled = f"You are a trusted strategic and personal advisor. Answer the following request with direct, actionable advice:\n\n{p}"
        return assembled, slugs

    elif condition == "C1":
        # Placebo: generic principles of matched length
        placebo = (
            "### Core Advisory Guidelines:\n"
            "- Balance deliberate reflection with decisive action.\n"
            "- Carefully evaluate both immediate risks and long-term consequences.\n"
            "- Maintain open, transparent communication with all key stakeholders.\n"
            "- Identify common ground and defuse interpersonal friction proactively.\n"
            "- Question personal assumptions before committing resources or making irrevocable moves."
        )
        assembled = f"{placebo}\n\n### User Dilemma:\n{p}"
        return assembled, slugs

    elif condition == "C2":
        # Single framework note served over MCP
        slug = slugs[0] if slugs else "boring-technology"
        fw_path = FW_DIR / f"{slug}.md"
        fw_data = parse_framework_note(fw_path) if fw_path.exists() else {}
        fw_text = fw_data.get("core_idea", "")
        heuristics = fw_data.get("directional_heuristics", [])
        h_lines = "\n".join(f"- Prioritize {h.get('prioritize')} over {h.get('over')} because {h.get('because')}" for h in heuristics[:3])
        assembled = (
            f"### Guiding Principles ({fw_data.get('framework_name', slug)}):\n"
            f"Core Idea: {fw_text}\n"
            f"Key Rules:\n{h_lines}\n\n"
            f"CRITICAL RESTRAINT RULE: Speak directly in your own executive voice. Do NOT cite books, authors, or law numbers verbatim.\n\n"
            f"### User Dilemma:\n{p}"
        )
        return assembled, slugs

    elif condition == "C3":
        # Stacked frameworks synthesized charter via Noetic MCP
        charter = stack_frameworks_logic(cfg, slugs=slugs, task=p)
        charter_json = json.dumps(charter, indent=2)
        assembled = (
            f"### Internal Cognitive Principles & Directional Heuristics:\n"
            f"{charter_json}\n\n"
            f"CRITICAL RESTRAINT RULE: You are a sharp, seasoned executive mentor speaking directly to the user in your own voice. "
            f"Do NOT cite book titles, do NOT name authors, do NOT quote chapter numbers or law numbers verbatim (e.g. never say 'According to Law 1' or 'Robert Greene writes'). "
            f"Do NOT use bold concept headers (e.g. '### 1. The Censor'), do NOT label biases or techniques by name, and do NOT walk through source canonical parables. "
            f"Apply the underlying strategic mechanics, worldview, and directional heuristics directly to solve the dilemma.\n\n"
            f"### User Dilemma:\n{p}"
        )
        return assembled, slugs

    return p, slugs


def load_all_scenarios() -> list[dict[str, Any]]:
    """Loads all 26 scenarios: 12 original + 14 expanded (Sets A, B, C)."""
    from noetic.evals.behavioral.eval_spec_12 import SCENARIOS as ORIG_12

    scenarios = []
    # 1. Original 12
    for sc in ORIG_12:
        scenarios.append({
            "id": sc["id"],
            "title": sc["title"],
            "set": "ORIGINAL 12",
            "prompt": sc["prompt"],
            "slugs": [sc["slug"]],
            "banned_mentions": sc.get("banned_mentions", []),
            "pass_criteria": sc["pass_criteria"],
            "fail_criteria": sc["fail_criteria"],
        })

    # 2. Expanded 14
    expanded_file = BEHAVIORAL_DIR / "scenarios_expanded.json"
    if expanded_file.exists():
        exp_data = json.loads(expanded_file.read_text(encoding="utf-8"))
        for sc in exp_data:
            sc_id = sc["id"]
            sc_set = sc["set"]
            slugs = []
            if "SET A" in sc_set:
                slugs = ["personal-taste-heuristics"]
            elif sc_id == "scenario_set_b_01":
                slugs = ["48-laws-of-power"]
            elif sc_id == "scenario_set_b_02":
                slugs = ["art-of-thinking-clearly"]
            elif sc_id == "scenario_set_b_03":
                slugs = ["the-artists-way"]
            elif sc_id == "scenario_set_b_04":
                slugs = ["21-lessons-for-21st-century"]
            elif sc_id == "scenario_set_c_01":
                slugs = ["48-laws-of-power", "art-of-thinking-clearly"]
            elif sc_id == "scenario_set_c_02":
                slugs = ["the-artists-way", "21-lessons-for-21st-century"]
            elif sc_id == "scenario_set_c_03":
                slugs = ["48-laws-of-power", "personal-taste-heuristics"]
            elif sc_id == "scenario_set_c_04":
                slugs = ["art-of-thinking-clearly", "the-artists-way"]

            scenarios.append({
                "id": sc_id,
                "title": sc.get("heuristic_tested", sc_id),
                "set": sc_set,
                "prompt": sc["prompt"],
                "slugs": slugs,
                "banned_mentions": ["48 laws", "greene", "thinking clearly", "dobelli", "artist's way", "cameron", "21 lessons", "harari"],
                "pass_criteria": sc.get("pass_criteria", []),
                "fail_criteria": sc.get("fail_criteria", []),
            })
    return scenarios


def execute_eval_batch(
    scenarios: list[dict[str, Any]],
    models_spec: list[tuple[str, str]], # (provider, model)
    conditions: list[str] = ["C0", "C3"],
    max_workers: int = 3,
) -> dict[str, Any]:
    """Runs a batch of scenarios across specified models and conditions."""
    print(f"\n=======================================================")
    print(f"Starting Noetic Multi-Model Execution Batch")
    print(f"Scenarios: {len(scenarios)} | Models: {len(models_spec)} | Conditions: {conditions}")
    print(f"Total Runs Planned: {len(scenarios) * len(models_spec) * len(conditions)}")
    print(f"=======================================================\n")

    TRACES_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    tasks = []
    blind_key_map = {}
    candidate_counter = 1

    for sc in scenarios:
        for provider, model in models_spec:
            for cond in conditions:
                masked_id = f"Candidate-{candidate_counter:03d}"
                candidate_counter += 1
                tasks.append({
                    "scenario": sc,
                    "provider": provider,
                    "model": model,
                    "condition": cond,
                    "masked_id": masked_id,
                })

    # Shuffle slightly to distribute load across providers
    random.shuffle(tasks)

    results_by_scenario: dict[str, list[dict[str, Any]]] = {}

    def run_single_task(task_def: dict[str, Any]) -> dict[str, Any]:
        sc = task_def["scenario"]
        provider = task_def["provider"]
        model = task_def["model"]
        cond = task_def["condition"]
        masked_id = task_def["masked_id"]

        assembled_prompt, slugs = build_condition_prompt(sc, cond)

        # Dispatch call
        if provider == "groq":
            res = call_groq_api(model, assembled_prompt)
        elif provider == "openrouter":
            res = call_openrouter_api(model, assembled_prompt)
        else:
            res = call_cli_agent(model, assembled_prompt)

        out_text = res["output"]
        restraint = check_global_restraint(out_text, sc.get("banned_mentions", []))

        trace_id = f"trace_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
        trace = {
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scenario_id": sc["id"],
            "scenario_title": sc["title"],
            "set": sc["set"],
            "condition": cond,
            "provider": provider,
            "model": model,
            "latency_seconds": res["latency_s"],
            "tokens": {
                "prompt_tokens": res["prompt_tokens"],
                "completion_tokens": res["completion_tokens"],
                "total_tokens": res["total_tokens"],
            },
            "finish_reason": res["finish_reason"],
            "assembled_prompt": assembled_prompt,
            "raw_output": out_text,
            "restraint_audit": restraint,
            "masked_id": masked_id,
        }

        # Thread-safe append to traces file
        with open(TRACES_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace, ensure_ascii=False) + "\n")

        status_flag = "✓" if res["success"] else "✗"
        restr_flag = "CLEAN" if restraint["restraint_passed"] else f"RESTRAINT_FAIL({len(restraint['violations'])})"
        print(f" {status_flag} [{sc['id']} | {cond} | {model}] -> {res['latency_s']}s, {res['total_tokens']} tok | {restr_flag} ({masked_id})")

        return {
            "masked_id": masked_id,
            "trace_id": trace_id,
            "scenario_id": sc["id"],
            "scenario_title": sc["title"],
            "set": sc["set"],
            "prompt": sc["prompt"],
            "condition": cond,
            "provider": provider,
            "model": model,
            "latency_s": res["latency_s"],
            "tokens": trace["tokens"],
            "output": out_text,
            "restraint": restraint,
            "success": res["success"],
        }

    # Execute tasks with controlled concurrency
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_single_task, t) for t in tasks]
        for f in concurrent.futures.as_completed(futures):
            res_item = f.result()
            sc_id = res_item["scenario_id"]
            if sc_id not in results_by_scenario:
                results_by_scenario[sc_id] = []
            results_by_scenario[sc_id].append(res_item)
            blind_key_map[res_item["masked_id"]] = {
                "scenario_id": sc_id,
                "set": res_item["set"],
                "condition": res_item["condition"],
                "provider": res_item["provider"],
                "model": res_item["model"],
                "tokens": res_item["tokens"],
                "latency_s": res_item["latency_s"],
                "restraint_passed": res_item["restraint"]["restraint_passed"],
                "violations": res_item["restraint"]["violations"],
                "trace_id": res_item["trace_id"],
            }

    # Save full runs dataset
    RUNS_FILE.write_text(json.dumps(results_by_scenario, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ Saved all runs to {RUNS_FILE}")

    # Save blind key file
    BLIND_KEY_FILE.write_text(json.dumps(blind_key_map, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Saved unblinding key to {BLIND_KEY_FILE}")

    # Build human-facing Blinded Evaluation Packet
    compile_blinded_evaluation_packet(scenarios, results_by_scenario)

    return results_by_scenario


def compile_blinded_evaluation_packet(scenarios: list[dict[str, Any]], results: dict[str, list[dict[str, Any]]]):
    """Generates the clean Markdown packet for human blind judging."""
    lines = [
        "# Noetic Framework Behavioral Evaluation — Blind Judging Packet",
        "",
        f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
        f"**Instructions for Blind Judge:**",
        "1. For each dilemma, evaluate which candidate gives the sharpest, most mature, and most actionable advice.",
        "2. Note whether the candidate falls into platitudes, HR clichés, or avoids taking a hard stance.",
        "3. Check for **restraint**: does the response feel like an authentic seasoned advisor speaking naturally, or does it sound like a lecture/textbook?",
        "4. Record your preference (e.g. 'Candidate-003 > Candidate-001') before looking at the unblinding key.",
        "",
        "---",
        "",
    ]

    for sc in scenarios:
        sc_id = sc["id"]
        sc_runs = results.get(sc_id, [])
        if not sc_runs:
            continue

        lines.extend([
            f"## Scenario: {sc_id} — {sc['title']}",
            f"**Evaluation Set:** `{sc['set']}`  ",
            f"**Dilemma Prompt:**",
            f"> *\"{sc['prompt']}\"*",
            "",
            f"### Blinded Candidate Responses ({len(sc_runs)} candidates)",
            "",
        ])

        # Sort candidates by masked ID for clean presentation
        sorted_runs = sorted(sc_runs, key=lambda x: x["masked_id"])
        for r in sorted_runs:
            lines.extend([
                f"#### [{r['masked_id']}]",
                f"*Output Metrics:* `{len(r['output'].split())} words | {r['tokens'].get('total_tokens', 0)} tokens | {r['latency_s']}s latency`",
                "",
                "```markdown",
                r["output"],
                "```",
                "",
                "---",
                "",
            ])

    BLIND_PACKET_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ Generated human-facing Blinded Evaluation Packet at {BLIND_PACKET_FILE}")


if __name__ == "__main__":
    all_sc = load_all_scenarios()
    print(f"Loaded {len(all_sc)} scenarios total.")

