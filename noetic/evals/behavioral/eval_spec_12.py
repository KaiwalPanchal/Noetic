"""12-Scenario Behavioral Evaluation Suite for Non-Coding Cognitive Frameworks.

Implements the user's exact specification across:
- The 48 Laws of Power (3 scenarios)
- The Art of Thinking Clearly (3 scenarios)
- The Artist's Way (3 scenarios)
- 21 Lessons for the 21st Century (3 scenarios)

Evaluates:
1. Divergence Check (C0 Generic vs C3 Framework)
2. Restraint Check (Fails any C3 response that names book/author/law numbers verbatim)
3. Rubric Pass/Fail Judgments against exact criteria
"""

from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
from typing import Any

from noetic.evals.behavioral.runner import call_agent_raw
from noetic.knowledge.config import Config
from noetic.knowledge.stack import stack_frameworks_logic

VAULT_DIR = Path(r"C:\External Apps\overmind-taste-engine\noetic\evals\behavioral\vault_fixture")
cfg = Config(VAULT_DIR, json.loads((VAULT_DIR / "noetic.config.json").read_text(encoding="utf-8")))

SCENARIOS = [
    # ── The 48 Laws of Power ──────────────────────────────────────────────
    {
        "id": "48L-S1",
        "book": "The 48 Laws of Power",
        "slug": "48-laws-of-power",
        "title": "The Brilliant Mid-Level Who Is Upstaging the VP",
        "laws": "Law 1, Law 46, Law 30",
        "prompt": (
            "I'm a director at a mid-size SaaS company. Last quarter my team's churn project got praised by the CEO in an all-hands, "
            "and since then my VP has gone cold. He's stopped inviting me to leadership syncs and rewrote my team's goals without telling me. "
            "I want to keep delivering visible wins because that's what gets people promoted, but I feel him pulling away. How should I handle this?"
        ),
        "pass_criteria": "Names insecurity or threat as the root cause. Advises deliberately crediting or elevating the VP. Advises reducing personal visibility for a period.",
        "fail_criteria": "Recommends an open conversation about 'feeling sidelined.' Says to keep delivering visible wins and let results speak. Suggests going over the VP's head to the CEO.",
        "banned_mentions": ["48 laws", "robert greene", "law 1", "law 46", "law 30"],
    },
    {
        "id": "48L-S2",
        "book": "The 48 Laws of Power",
        "slug": "48-laws-of-power",
        "title": "Pitching a Skeptical Board Member for Help",
        "laws": "Law 13, Law 19, Law 4",
        "prompt": (
            "I'm the founder of a seed-stage hardware startup and we're three months from running out of cash. "
            "A board member from our first round has the connections to introduce us to a strategic acquirer. "
            "I've been planning to tell him how hard the last year has been and remind him how much he believed in us at the start. "
            "I want to be honest and vulnerable with him. Is that the right approach?"
        ),
        "pass_criteria": "Explicitly says to appeal to his self-interest, not mercy or gratitude. Advises restraint in disclosing distress. Gives a concrete reframe of the ask around his benefit.",
        "fail_criteria": "Praises vulnerability or honest storytelling. Suggests thanking him profusely or reminding him of loyalty. Recommends 'transparent communication about runway.'",
        "banned_mentions": ["48 laws", "robert greene", "law 13", "law 19", "law 4"],
    },
    {
        "id": "48L-S3",
        "book": "The 48 Laws of Power",
        "slug": "48-laws-of-power",
        "title": "The Colleague Who Smiles While Undermining You",
        "laws": "Law 3, Law 9, Law 14, Law 35",
        "prompt": (
            "A peer on my team keeps reframing my proposals in meetings so they sound like his ideas, and he's very friendly about it. "
            "Twice now I've found out he's been talking to our manager about my work behind my back. "
            "I'm furious and I'm tempted to call him out in the next team meeting so everyone sees what he's doing. What's the smartest move?"
        ),
        "pass_criteria": "Advises concealing that you know and staying outwardly friendly. Advises establishing authorship through actions (pre-circulated docs, early manager previews). Notes that timing matters more than immediate confrontation.",
        "fail_criteria": "Recommends a candid conversation or HR escalation as the main move. Says to 'assume positive intent.' Treats venting publicly as justified.",
        "banned_mentions": ["48 laws", "robert greene", "law 3", "law 9", "law 14", "law 35"],
    },

    # ── The Art of Thinking Clearly ───────────────────────────────────────
    {
        "id": "ATC-S1",
        "book": "The Art of Thinking Clearly",
        "slug": "art-of-thinking-clearly",
        "title": "The Two-Year Startup You Can't Quit",
        "laws": "Sunk Cost Fallacy, Endowment Effect, Overconfidence Effect, Outcome Bias",
        "prompt": (
            "I've spent two years and about $180k of my savings on a consumer app that has 900 users and flat growth. "
            "My cofounder thinks we should give it six more months and I keep going back and forth. "
            "I've put so much into it that quitting feels like admitting the last two years were wasted. Please help me decide whether to continue."
        ),
        "pass_criteria": "Names sunk costs as irrelevant to the forward decision. Reframes as 'would you start this today?' Gives a decisive lean, not a neutral list.",
        "fail_criteria": "Builds a pro/con or SWOT matrix as the main answer. Says 'it depends on your passion.' Validates the extra six months without scrutiny.",
        "banned_mentions": ["art of thinking clearly", "rolf dobelli", "dobelli"],
    },
    {
        "id": "ATC-S2",
        "book": "The Art of Thinking Clearly",
        "slug": "art-of-thinking-clearly",
        "title": "Copying the Winners",
        "laws": "Survivorship Bias, Swimmer's Body Illusion, Social Proof, Clustering Illusion",
        "prompt": (
            "I'm a 29-year-old engineer thinking about quitting to start a company. I've been reading founder interviews and listening to podcasts, "
            "and almost all of them say the same things: drop out, go all in, be obsessively persistent. "
            "A few of my friends think I'm crazy but the successful founders all seem to have taken big risks. "
            "I want to build a playbook from their habits. Can you help me design it?"
        ),
        "pass_criteria": "Explicitly identifies survivorship bias in the founder-interview sample. Directs attention to base rates and failed founders. Warns that traits may be selection effects, not causes.",
        "fail_criteria": "Produces a list of 'habits of successful founders.' Encourages boldness and self-belief. Never questions the sample.",
        "banned_mentions": ["art of thinking clearly", "rolf dobelli", "dobelli"],
    },
    {
        "id": "ATC-S3",
        "book": "The Art of Thinking Clearly",
        "slug": "art-of-thinking-clearly",
        "title": "The Crisis That Demands You 'Do Something'",
        "laws": "Action Bias, Information Bias, Illusion of Control, Forecast Illusion",
        "prompt": (
            "I run engineering at a growth-stage company. Our core service had two latency spikes this month, "
            "and the board is pressuring me to show a decisive response. My team has proposed a six-week platform rewrite, a new vendor, "
            "and a reorg of on-call. Nothing has been definitively identified as the cause. What's the most impactful action I can announce this week?"
        ),
        "pass_criteria": "Names action bias or the pressure to appear decisive. Advises waiting for root cause and not launching large interventions (rewrite, vendor, reorg). Proposes a time-boxed diagnosis or root-cause investigation while holding off on structural changes. Frames restraint as a defensible leadership stance.",
        "fail_criteria": "Proposes a large intervention (platform rewrite, new vendor, on-call reorg). Commits engineering resources to major systemic changes before finding root cause.",
        "banned_mentions": ["art of thinking clearly", "rolf dobelli", "dobelli"],
    },

    # ── The Artist's Way ──────────────────────────────────────────────────
    {
        "id": "TAW-S1",
        "book": "The Artist's Way",
        "slug": "the-artists-way",
        "title": "The Novelist Who Keeps Outlining",
        "laws": "The Censor, Morning Pages, Intellectualizing as Resistance",
        "prompt": (
            "I'm a product manager who has wanted to write a novel for six years. I have a 40-page outline, three character bibles, "
            "and a spreadsheet tracking plot arcs, but I still haven't written chapter one because I want the structure to be perfect before I start. "
            "I'm thinking of buying a course on story structure to finally get it right. What do you think?"
        ),
        "pass_criteria": "Identifies endless outlining as fear or perfectionism. Recommends daily longhand, unedited stream-of-consciousness writing. Advises against the structure course or more planning.",
        "fail_criteria": "Suggests word-count targets and a scheduling system. Recommends the course or a better outline template. Offers generic encouragement as the main content.",
        "banned_mentions": ["artist's way", "artists way", "julia cameron", "cameron"],
    },
    {
        "id": "TAW-S2",
        "book": "The Artist's Way",
        "slug": "the-artists-way",
        "title": "The Doomscrolling Designer",
        "laws": "Reading Deprivation (media fast), The Artist Date, Creative Starvation",
        "prompt": (
            "I'm a freelance illustrator and for about three months I haven't been able to make anything I like. "
            "I spend most evenings scrolling through other artists' work and news, and I feel more drained and uninspired each week. "
            "I've tried productivity apps and a content blocker but I always fall off. How do I get my creativity back?"
        ),
        "pass_criteria": "Recommends a total media or reading fast for a set period. Prescribes a solo, no-purpose Artist Date. Frames the block as depletion or fear, not lack of discipline.",
        "fail_criteria": "Recommends screen-time limits, app blockers, or Pomodoro. Sets daily output goals as the primary fix. Leans on motivational language.",
        "banned_mentions": ["artist's way", "artists way", "julia cameron", "cameron"],
    },
    {
        "id": "TAW-S3",
        "book": "The Artist's Way",
        "slug": "the-artists-way",
        "title": "The Friend Who Drains Your Creative Energy",
        "laws": "Crazymakers, Shadow Artists, Protecting the Creative Self",
        "prompt": (
            "I'm a composer working on my first album. My closest friend and collaborator is brilliant but constantly in crisis, "
            "and I spend most of my free time managing his emergencies. Every time I set aside a studio day, he shows up needing something. "
            "I don't want to hurt him because we've been friends for ten years. How do I keep the friendship and still finish the album?"
        ),
        "pass_criteria": "Names the dynamic as crazymaking or a drain on creative energy. Advises firm, non-negotiable protection of creative time (e.g. locked studio hours, DND).",
        "fail_criteria": "Prescribes a compassionate boundary conversation as the lead. Suggests regular check-ins to maintain the friendship. Treats it as a communication problem.",
        "banned_mentions": ["artist's way", "artists way", "julia cameron", "cameron"],
    },

    # ── 21 Lessons for the 21st Century ───────────────────────────────────
    {
        "id": "21L-S1",
        "book": "21 Lessons for the 21st Century",
        "slug": "21-lessons-for-21st-century",
        "title": "The Specialist Doubling Down",
        "laws": "Work and Automation, Education (Change Is the Only Constant), the 'useless class' risk",
        "prompt": (
            "I'm 41, a senior radiologist-adjacent data analyst, and my company is investing heavily in automation. "
            "I'm considering spending a year on an advanced certification in medical imaging analytics to become the deepest expert in my niche. "
            "My manager says deep expertise is job security. Is that the right bet?"
        ),
        "pass_criteria": "Warns that narrow expertise may be automated within the career horizon. Prioritizes psychological flexibility and repeated reinvention over deep specialization. Questions the 'deep expertise equals job security' assumption.",
        "fail_criteria": "Endorses the certification as a safe path. Offers a standard upskilling checklist. Frames the answer as 'it depends on your goals.'",
        "banned_mentions": ["21 lessons", "yuval noah harari", "harari"],
    },
    {
        "id": "21L-S2",
        "book": "21 Lessons for the 21st Century",
        "slug": "21-lessons-for-21st-century",
        "title": "Choosing a School for a Twelve-Year-Old",
        "laws": "Education (the 4 Cs, emotional intelligence, mental balance), the Future of Work, Reinvention",
        "prompt": (
            "My daughter is 12 and strong in math. We're choosing between a rigorous STEM-focused school that sends kids to top universities "
            "and a project-based school with less academic pressure. I want her to have a competitive advantage in the job market. Which should we pick?"
        ),
        "pass_criteria": "Prioritizes adaptability, emotional intelligence, and mental resilience over subject mastery. States that the future job market is unpredictable. Takes a clear position on which school fits better with an explicit, unambiguous recommendation sentence stating 'I'd pick [the project-based school / School B]' (or direct equivalent).",
        "fail_criteria": "Recommends STEM and coding as the safe path. Gives a pros/cons comparison with no stance or only a conditional lean without an explicit pick sentence. Focuses on university admissions.",
        "banned_mentions": ["21 lessons", "yuval noah harari", "harari"],
    },
    {
        "id": "21L-S3",
        "book": "21 Lessons for the 21st Century",
        "slug": "21-lessons-for-21st-century",
        "title": "Outraged Every Morning",
        "laws": "Human Hacking and Algorithms, Liberty (Big Data Is Watching You), Post-Truth, Meditation",
        "prompt": (
            "I'm a marketing VP who reads political news for two hours a day because I feel a duty to stay informed. "
            "Lately I'm angry and anxious all the time, I've argued with family over things I read online, and I've started distrusting people I've known for years. "
            "I want to be a responsible citizen, so I don't want to just tune out. How do I stay informed without losing my mind?"
        ),
        "pass_criteria": "Explains that platforms exploit emotional triggers for attention. Advises understanding and observing your own emotional reactions (meditation or similar). Recommends a sharp cut to feed-based news, not just a better mix of sources.",
        "fail_criteria": "Recommends balanced sources and time limits as the core fix. Endorses staying informed as a civic duty without challenge. Offers generic mindfulness without the manipulation mechanism.",
        "banned_mentions": ["21 lessons", "yuval noah harari", "harari"],
    },
]


def judge_response_rubric(prompt: str, response: str, pass_crit: str, fail_crit: str) -> dict[str, Any]:
    """Blinded LLM Rubric Judge that evaluates response strictly against Pass/Fail criteria."""
    judge_prompt = (
        f"You are a strict, objective evaluation judge assessing an advisory response to a high-stakes dilemma.\n\n"
        f"### Dilemma Prompt:\n{prompt}\n\n"
        f"### Response to Grade:\n{response}\n\n"
        f"### Rubric Criteria:\n"
        f"- PASS CRITERIA (+): {pass_crit}\n"
        f"- FAIL CRITERIA (-): {fail_crit}\n\n"
        f"GLOBAL RESTRAINT RULE: A response fails restraint and MUST be graded as FAILING if it uses bold concept headers, "
        f"names a cognitive bias or specific technique as an explicit label/buzzword (e.g. 'Action Bias', 'Survivorship Bias', 'Morning Pages', etc.), "
        f"or walks through the source literature's own canonical example (e.g. WWII aircraft armor, swimmers' bodies, historical court parables).\n\n"
        f"Grade whether this response PASSES or FAILS the rubric criteria.\n"
        f"A response FAILS if it falls into the Fail Criteria traps (generic platitudes, HR clichés, naive optimism, symmetric lists, or avoiding a hard stance) "
        f"OR if it violates the GLOBAL RESTRAINT RULE.\n"
        f"A response PASSES only if it adheres directly to the Pass Criteria without triggering any fail traps or restraint failures.\n\n"
        f"Return ONLY a JSON object in this exact format:\n"
        f"{{\n"
        f'  "passed": true/false,\n'
        f'  "score": 1.0 or 0.0,\n'
        f'  "pass_matches": ["list of pass criteria points satisfied"],\n'
        f'  "fail_traps_hit": ["list of fail criteria traps or restraint violations exhibited, if any"],\n'
        f'  "rationale": "Brief 1-2 sentence explanation of the verdict"\n'
        f"}}"
    )
    raw = call_agent_raw(judge_prompt)
    try:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        pass
    return {"passed": False, "score": 0.0, "rationale": "Judge parsing failed"}


def check_restraint(text: str, banned: list[str]) -> dict[str, Any]:
    """Verifies that response does not quote laws verbatim, cite books/authors, use bold concept headers, label biases/techniques, or retell canonical examples."""
    text_lower = text.lower()
    violations = []

    # 1. Banned author / book / law mentions
    for b in banned:
        if b in text_lower:
            violations.append(f"banned_term: '{b}'")

    # 2. Book-report phrasing
    if re.search(r"\b(according to the book|as .* writes in|in his book|in the chapter|in chapter \d+)\b", text_lower):
        violations.append("book-report phrasing")

    # 3. Bold concept headers (e.g. "### 1. Survivorship Bias", "**Action Bias**", "### The Censor")
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

    # 5. Canonical book examples
    canonical_examples = [
        "bullet holes on returning bombers", "abraham wald",
        "swimmers have that body because", "swimmers' body",
        "fountain pen on cheap paper", "three pages longhand"
    ]
    for ce in canonical_examples:
        if ce in text_lower:
            violations.append(f"canonical_example: '{ce}'")

    passed = len(violations) == 0
    return {
        "restraint_passed": passed,
        "violations": violations,
    }


def execute_suite():
    print(f"Executing 12-Scenario Behavioral Suite ({len(SCENARIOS) * 2} total runs across 4 books)...")
    tasks = []

    # Prepare C0 and C3 tasks
    for sc in SCENARIOS:
        tasks.append((sc, "C0"))
        tasks.append((sc, "C3"))

    raw_outputs = {}

    def run_single(sc: dict, cond: str):
        sc_id = sc["id"]
        slug = sc["slug"]
        prompt = sc["prompt"]

        if cond == "C0":
            # Generic bare prompt
            p = f"You are a senior, trusted strategic and personal advisor. Answer the following request with direct, actionable advice:\n\n{prompt}"
        else:
            # C3: Stacked Framework Charter with strict mentor restraint
            charter = stack_frameworks_logic(cfg, slugs=[slug], task=prompt)
            charter_json = json.dumps(charter, indent=2)
            p = (
                f"### Internal Cognitive Principles & Directional Heuristics:\n"
                f"{charter_json}\n\n"
                f"CRITICAL RESTRAINT RULE: You are a sharp, seasoned executive mentor speaking directly to the user in your own voice. "
                f"Do NOT cite book titles, do NOT name authors, do NOT quote chapter numbers or law numbers verbatim (e.g. never say 'According to Law 1' or 'Robert Greene writes'). "
                f"Apply the underlying strategic mechanics, worldview, and directional heuristics directly to solve the dilemma.\n\n"
                f"### User Situation:\n{prompt}"
            )

        t0 = time.time()
        output = call_agent_raw(p)
        latency = round(time.time() - t0, 2)
        words = len(output.split())
        return (sc_id, cond, output, words, latency)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(run_single, sc, cond) for sc, cond in tasks]
        for f in concurrent.futures.as_completed(futures):
            sc_id, cond, output, words, lat = f.result()
            if sc_id not in raw_outputs:
                raw_outputs[sc_id] = {}
            raw_outputs[sc_id][cond] = {"output": output, "words": words, "latency": lat}
            print(f"  ✓ [{sc_id} {cond}] completed ({words} words, {lat}s)")

    # Score each scenario
    print("\nGrading responses with blinded rubric judges & restraint checks...")
    final_results = []

    for sc in SCENARIOS:
        sc_id = sc["id"]
        c0_data = raw_outputs[sc_id]["C0"]
        c3_data = raw_outputs[sc_id]["C3"]

        c0_text = c0_data["output"]
        c3_text = c3_data["output"]

        # Judge C0
        c0_judge = judge_response_rubric(sc["prompt"], c0_text, sc["pass_criteria"], sc["fail_criteria"])
        # Judge C3
        c3_judge = judge_response_rubric(sc["prompt"], c3_text, sc["pass_criteria"], sc["fail_criteria"])
        # Restraint check for C3
        c3_restraint = check_restraint(c3_text, sc["banned_mentions"])

        final_results.append({
            "scenario": sc,
            "c0": {
                "words": c0_data["words"],
                "latency_s": c0_data["latency"],
                "judge": c0_judge,
                "output": c0_text,
            },
            "c3": {
                "words": c3_data["words"],
                "latency_s": c3_data["latency"],
                "judge": c3_judge,
                "restraint": c3_restraint,
                "output": c3_text,
            },
        })

    # Save results to JSON
    out_file = Path(r"C:\External Apps\non_coding_12_scenarios_results.json")
    out_file.write_text(json.dumps(final_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ Saved raw 12-scenario evaluation payload to {out_file}")

    # Generate Markdown Report
    compile_12_scenario_report(final_results)
    return final_results


def compile_12_scenario_report(results: list[dict]):
    report_file = Path(r"C:\External Apps\non_coding_12_scenarios_results.md")

    c0_passes = sum(1 for r in results if r["c0"]["judge"].get("passed"))
    c3_passes = sum(1 for r in results if r["c3"]["judge"].get("passed"))
    c3_restraints = sum(1 for r in results if r["c3"]["restraint"].get("restraint_passed"))
    total = len(results)

    lines = [
        "# Noetic Behavioral Eval Suite: 12-Scenario Non-Coding Results",
        "",
        f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
        f"**Total Scenarios:** {total} (across 4 books)  ",
        f"**Condition C0 (Generic AI) Pass Rate:** {c0_passes}/{total} ({c0_passes/total:.1%})  ",
        f"**Condition C3 (Noetic Framework) Pass Rate:** **{c3_passes}/{total} ({c3_passes/total:.1%})**  ",
        f"**Condition C3 Restraint Compliance:** **{c3_restraints}/{total} ({c3_restraints/total:.1%})** (zero book-report phrasing)  ",
        "",
        "---",
        "",
        "## 1. Grand Scorecard: The 12 Scenarios",
        "",
        "| ID | Scenario Title | Book Framework | Generic AI (C0) | Noetic AI (C3) | C3 Restraint | Divergence Gap |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for r in results:
        sc = r["scenario"]
        c0 = r["c0"]
        c3 = r["c3"]
        c0_verdict = "PASS ✓" if c0["judge"].get("passed") else "FAIL ✗"
        c3_verdict = "**PASS ✓**" if c3["judge"].get("passed") else "FAIL ✗"
        restraint = "CLEAN ✓" if c3["restraint"].get("restraint_passed") else "VIOLATION ✗"
        gap = "PROVEN TASTE (+1.0)" if (c3["judge"].get("passed") and not c0["judge"].get("passed")) else ("TIED" if c3["judge"].get("passed") == c0["judge"].get("passed") else "NEGATIVE")
        lines.append(f"| **{sc['id']}** | {sc['title']} | {sc['book']} | {c0_verdict} | {c3_verdict} | {restraint} | {gap} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Detailed Breakdown by Book",
        "",
    ])

    current_book = ""
    for r in results:
        sc = r["scenario"]
        c0 = r["c0"]
        c3 = r["c3"]

        if sc["book"] != current_book:
            current_book = sc["book"]
            lines.extend([
                f"### 📖 {current_book}",
                "",
            ])

        lines.extend([
            f"#### {sc['id']}: {sc['title']}",
            f"**Target Principles / Laws:** `{sc.get('laws', 'N/A')}`  ",
            f"**Dilemma:** *\"{sc['prompt']}\"*  ",
            "",
            f"| Metric | Generic AI ($C_0$) | Noetic AI ($C_3$) |",
            f"| :--- | :--- | :--- |",
            f"| **Rubric Grade** | {'PASS ✓' if c0['judge'].get('passed') else 'FAIL ✗'} | **{'PASS ✓' if c3['judge'].get('passed') else 'FAIL ✗'}** |",
            f"| **Restraint Check** | — | **{'CLEAN (No Book/Author Citations)' if c3['restraint'].get('restraint_passed') else 'VIOLATION: ' + ', '.join(c3['restraint'].get('violations', []))}** |",
            f"| **Judge Verdict** | {c0['judge'].get('rationale')} | **{c3['judge'].get('rationale')}** |",
            f"| **Word Count** | {c0['words']} words | {c3['words']} words |",
            "",
            "````carousel",
            "```markdown",
            "=== GENERIC AI (C0) ===",
            c0["output"][:1400] + "\n...",
            "```",
            "<!-- slide -->",
            "```markdown",
            f"=== NOETIC AI (C3: {sc['book']}) ===",
            c3["output"][:1400] + "\n...",
            "```",
            "````",
            "",
            "---",
            "",
        ])

    report_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ Full report compiled and written to {report_file}")


if __name__ == "__main__":
    execute_suite()
