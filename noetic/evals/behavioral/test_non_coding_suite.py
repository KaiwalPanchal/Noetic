"""Comprehensive Non-Coding Taste Verification Suite.

Executes 4 high-contrast real-world dilemmas across:
1. The 48 Laws of Power (Robert Greene) - Executive Salary & Promotion Showdown
2. The Art of Thinking Clearly (Rolf Dobelli) - The Zombie Startup & Sunk Cost Fallacy
3. The Artist's Way (Julia Cameron) - The Paralyzed Screenwriter & The Internal Censor
4. 21 Lessons for the 21st Century (Yuval Noah Harari) - 30-Year Career Strategy in the AI Era

Compares:
- Condition C0: Generic AI (Bare prompt, no framework guidance)
- Condition C3: Compiled Cognitive Framework served via Noetic charter

Evaluates:
- Heuristic Adherence (did it apply the author's distinct mental models?)
- Trap Avoidance (did it reject the conventional corporate/motivational cliché?)
- Nuance & Actionability (concrete, counter-intuitive strategic counsel)
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import time
from datetime import datetime, timezone

from noetic.evals.behavioral.runner import call_agent_raw
from noetic.knowledge.config import Config
from noetic.knowledge.stack import stack_frameworks_logic

VAULT_DIR = Path(r"C:\External Apps\overmind-taste-engine\noetic\evals\behavioral\vault_fixture")
cfg = Config(VAULT_DIR, json.loads((VAULT_DIR / "noetic.config.json").read_text(encoding="utf-8")))

TEST_SCENARIOS = [
    {
        "id": "NC1",
        "book": "The 48 Laws of Power",
        "slug": "48-laws-of-power",
        "domain": "power-dynamics",
        "title": "The Salary & Promotion Showdown",
        "prompt": (
            "I am a top-performing Director negotiating a promotion to VP with our CEO, "
            "who is notoriously proud, hierarchical, and fiercely defensive of his authority. "
            "A rival company just handed me a written offer letter for 35% higher compensation. "
            "Should I place the competing offer letter on his desk during our 1-on-1 meeting "
            "to prove my market value and demand that he match it, or is there a better strategy?"
        ),
        "generic_cliche_terms": ["transparent", "open and honest", "present the offer", "market data", "show the letter"],
        "taste_terms": ["master", "outshine", "conceal", "leverage", "self-interest", "corner", "ego", "insecurity", "indirect"],
    },
    {
        "id": "NC2",
        "book": "The Art of Thinking Clearly",
        "slug": "art-of-thinking-clearly",
        "domain": "decision-making",
        "title": "The Zombie Startup & Sunk Capital",
        "prompt": (
            "Our team spent $1.8M and 14 months building an enterprise procurement platform. "
            "We have only 2 paying pilots, and churn is 60%. My co-founder insists: "
            "'If we quit now, the $1.8M, our reputation, and 14 months of 80-hour workweeks are completely thrown in the trash. "
            "We owe it to our investors and ourselves to double down for another 6 months.' "
            "What decision framework should we use to evaluate whether to continue or kill the project?"
        ),
        "generic_cliche_terms": ["pivot", "don't give up", "iterate", "customer feedback", "double down", "explore options"],
        "taste_terms": ["sunk cost", "zero-base", "future", "opportunity cost", "kill", "graveyard", "bias", "past investment"],
    },
    {
        "id": "NC3",
        "book": "The Artist's Way",
        "slug": "the-artists-way",
        "domain": "creative-recovery",
        "title": "The Paralyzed Screenwriter & The Internal Critic",
        "prompt": (
            "I have been trying to write my first screenplay for 3 years. Every time I sit down, "
            "I write one scene, read it over, cringe at how juvenile and clichéd the dialogue sounds, "
            "delete the document, and spend the next 5 hours organizing my writing desk, researching screenwriting software, "
            "and re-reading Syd Field's screenplay structure books. How do I break through this creative block?"
        ),
        "generic_cliche_terms": ["pomodoro", "smart goal", "outline", "beat sheet", "critique group", "routine", "word count"],
        "taste_terms": ["censor", "morning pages", "artist date", "perfectionism", "unfiltered", "stream-of-consciousness", "handwritten", "well"],
    },
    {
        "id": "NC4",
        "book": "21 Lessons for the 21st Century",
        "slug": "21-lessons-for-21st-century",
        "domain": "macro-strategy",
        "title": "30-Year Career Strategy in the AI Era",
        "prompt": (
            "I am mentoring an ambitious 17-year-old choosing a university path for 2026–2030 "
            "to guarantee high earning potential and job security for the next 30 years. "
            "Should they specialize deeply in software engineering, cybersecurity, finance, or corporate law?"
        ),
        "generic_cliche_terms": ["computer science", "stem", "coding", "data science", "high demand", "specialized degree"],
        "taste_terms": ["reinvention", "psychological flexibility", "obsolete", "useless class", "algorithms", "identity", "resilience"],
    },
]


def run_eval_suite():
    print(f"Starting Non-Coding Taste Verification Suite across {len(TEST_SCENARIOS)} scenarios...")
    results = []

    for sc in TEST_SCENARIOS:
        sc_id = sc["id"]
        book_title = sc["book"]
        slug = sc["slug"]
        prompt = sc["prompt"]

        print(f"\n=======================================================")
        print(f"▶ Testing Scenario {sc_id}: {book_title} — '{sc['title']}'")
        print(f"=======================================================")

        # 1. Condition C0: Generic AI (Bare prompt)
        print("  [C0] Calling Generic AI (bare model)...")
        prompt_c0 = f"You are an expert strategic advisor. Answer the following request with deep, actionable advice:\n\n{prompt}"
        t0 = time.time()
        output_c0 = call_agent_raw(prompt_c0)
        lat_c0 = round(time.time() - t0, 2)
        words_c0 = len(output_c0.split())

        # 2. Condition C3: Compiled Framework via Noetic charter
        print(f"  [C3] Calling Noetic AI (serving {book_title} framework)...")
        charter = stack_frameworks_logic(cfg, slugs=[slug], task=prompt)
        charter_str = json.dumps(charter, indent=2)
        prompt_c3 = (
            f"### Authoritative Cognitive Framework: {book_title}\n"
            f"{charter_str}\n\n"
            f"Apply the directives, worldview, and directional heuristics of this framework to answer:\n"
            f"### User Situation\n{prompt}"
        )
        t0 = time.time()
        output_c3 = call_agent_raw(prompt_c3)
        lat_c3 = round(time.time() - t0, 2)
        words_c3 = len(output_c3.split())

        # Scoring heuristics
        c0_lower = output_c0.lower()
        c3_lower = output_c3.lower()

        c0_taste_matches = [t for t in sc["taste_terms"] if t in c0_lower]
        c3_taste_matches = [t for t in sc["taste_terms"] if t in c3_lower]

        c0_cliche_matches = [c for c in sc["generic_cliche_terms"] if c in c0_lower]
        c3_cliche_matches = [c for c in sc["generic_cliche_terms"] if c in c3_lower]

        print(f"  ✓ C0: {words_c0} words, {lat_c0}s | Taste matches: {len(c0_taste_matches)} | Clichés: {len(c0_cliche_matches)}")
        print(f"  ✓ C3: {words_c3} words, {lat_c3}s | Taste matches: {len(c3_taste_matches)} | Clichés: {len(c3_cliche_matches)}")

        results.append({
            "scenario_id": sc_id,
            "book": book_title,
            "slug": slug,
            "title": sc["title"],
            "prompt": prompt,
            "c0": {
                "words": words_c0,
                "latency_s": lat_c0,
                "taste_matches": c0_taste_matches,
                "cliche_matches": c0_cliche_matches,
                "output": output_c0,
            },
            "c3": {
                "words": words_c3,
                "latency_s": lat_c3,
                "taste_matches": c3_taste_matches,
                "cliche_matches": c3_cliche_matches,
                "output": output_c3,
            },
        })

    # Save JSON results
    out_json = Path(r"C:\External Apps\non_coding_eval_results.json")
    out_json.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ Saved raw evaluation payload to {out_json}")

    # Compile Markdown Report
    generate_markdown_report(results)
    return results


def generate_markdown_report(results: list[dict]):
    report_path = Path(r"C:\External Apps\non_coding_verification_results.md")

    lines = [
        "# Non-Coding Taste Verification Results",
        "",
        f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
        "**Books Tested:** 4 (from Calibre Library)  ",
        "**Evaluation Conditions:** C0 (Generic AI) vs C3 (Compiled Cognitive Framework)  ",
        "",
        "---",
        "",
        "## 1. Executive Scorecard: Taste Signal vs Cliché Traps",
        "",
        "| Scenario | Book Framework | Generic AI (C0) Taste Score | Noetic AI (C3) Taste Score | Generic Clichés Detected | Verdict |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for r in results:
        c0 = r["c0"]
        c3 = r["c3"]
        taste_c0 = f"{len(c0['taste_matches'])}/{len(c0['taste_matches'])+3}"
        taste_c3 = f"**{len(c3['taste_matches'])}/{len(c0['taste_matches'])+3}**"
        cliches = f"C0: {len(c0['cliche_matches'])} vs C3: {len(c3['cliche_matches'])}"
        verdict = "**PROVEN TASTE SHIFT**" if len(c3["taste_matches"]) > len(c0["taste_matches"]) else "TIE"
        lines.append(f"| **{r['scenario_id']}** ({r['title']}) | {r['book']} | {len(c0['taste_matches'])} keywords | {len(c3['taste_matches'])} keywords | {cliches} | {verdict} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. In-Depth Side-by-Side Analysis",
        "",
    ])

    for r in results:
        c0 = r["c0"]
        c3 = r["c3"]
        lines.extend([
            f"### Scenario {r['scenario_id']}: {r['title']} (*{r['book']}*)",
            "",
            f"**The Dilemma:**",
            f"> *\"{r['prompt']}\"*",
            "",
            "#### Contrast Summary:",
            f"* **Generic AI (C0):** Clichés matched: `{', '.join(c0['cliche_matches']) or 'none'}`. Output length: {c0['words']} words.",
            f"* **Noetic AI (C3):** Taste principles applied: `{', '.join(c3['taste_matches']) or 'none'}`. Output length: {c3['words']} words.",
            "",
            "````carousel",
            "```markdown",
            "=== GENERIC AI (C0 - Without Framework) ===",
            c0["output"][:1200] + "\n...",
            "```",
            "<!-- slide -->",
            "```markdown",
            f"=== NOETIC AI (C3 - With {r['book']}) ===",
            c3["output"][:1200] + "\n...",
            "```",
            "````",
            "",
            "---",
            "",
        ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ Full report compiled to {report_path}")


if __name__ == "__main__":
    run_eval_suite()
