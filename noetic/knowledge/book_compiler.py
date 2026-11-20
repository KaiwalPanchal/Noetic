"""Cumulative Multi-Pass Book Compiler.

Ingests full EPUB books through a 3-pass cumulative pipeline:
1. Pass 1: Macro-Blueprint (author thesis, domain primitives, structural arc)
2. Pass 2: Progressive Chapter Walk with Working Memory (tracks concept buildup,
   cross-references, and evolving heuristics)
3. Pass 3: Global Graph Synthesis (clusters, resolves contradictions, ranks top
   heuristics, and compiles canonical framework note).
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from noetic.evals.behavioral.runner import call_agent_raw
from noetic.tools.epub_reader import EpubReader


class BookCompiler:
    """Compiles EPUB books into Noetic Cognitive Frameworks using cumulative memory."""

    def __init__(self, epub_path: Path | str, title: str, author: str, domain: str = "general-strategy"):
        self.epub_path = Path(epub_path)
        self.title = title
        self.author = author
        self.domain = domain
        self.reader = EpubReader(self.epub_path)

    def compile(self, max_chapters: int = 15) -> dict[str, Any]:
        """Runs the 3-pass cumulative extraction pipeline."""
        chapters = self.reader.inspect_chapters()
        print(f"[{self.title}] Loaded {len(chapters)} chapters from EPUB.")

        # Pass 1: Macro-Blueprint
        blueprint = self._pass1_blueprint(chapters)
        print(f"  ✓ Pass 1 complete: Extracted Macro-Blueprint (Worldview & Primitives)")

        # Pass 2: Progressive Chapter Walk with Working Memory
        walk_results = self._pass2_chapter_walk(chapters[:max_chapters], blueprint)
        print(f"  ✓ Pass 2 complete: Processed {len(walk_results['heuristics'])} chapters with working memory")

        # Pass 3: Global Graph Synthesis
        framework_data = self._pass3_synthesis(blueprint, walk_results)
        print(f"  ✓ Pass 3 complete: Synthesized canonical Cognitive Framework")

        return framework_data

    def _pass1_blueprint(self, chapters: list[dict[str, Any]]) -> dict[str, Any]:
        """Pass 1: Reads intro/preface and table of contents to establish core thesis."""
        # Find introductory chapters or first 2 chapters
        intro_texts = []
        for c in chapters[:3]:
            intro_texts.append(f"### {c['title']}\n{c['text'][:3000]}")
        combined_intro = "\n\n".join(intro_texts)

        prompt = (
            f"You are a cognitive compiler analyzing the book '{self.title}' by {self.author}.\n"
            f"Here are excerpts from the book's opening and introductory chapters:\n\n"
            f"{combined_intro}\n\n"
            f"Analyze the author's macro-worldview and return a clean JSON object with:\n"
            f"1. 'core_worldview': A dense, 2-3 sentence synthesis of the author's primary thesis and perspective.\n"
            f"2. 'domain': Primary domain of application (e.g. power-dynamics, decision-making, creative-recovery).\n"
            f"3. 'primitives': Array of 3-5 core entities/forces the author operates on (name, kind: 'entity'|'variable'|'force'|'state', definition).\n\n"
            f"Return ONLY valid JSON."
        )

        resp = call_agent_raw(prompt)
        try:
            m = re.search(r"\{.*\}", resp, re.DOTALL)
            return json.loads(m.group(0)) if m else {}
        except Exception:
            return {
                "core_worldview": f"Core strategic philosophy of {self.title} by {self.author}.",
                "domain": self.domain,
                "primitives": [],
            }

    def _pass2_chapter_walk(self, chapters: list[dict[str, Any]], blueprint: dict[str, Any]) -> dict[str, Any]:
        """Pass 2: Sequentially walks chapters carrying rolling working memory."""
        working_memory = {
            "active_heuristics": [],
            "defined_concepts": {},
            "cross_references": [],
        }

        extracted_heuristics = []

        for idx, chapter in enumerate(chapters):
            ch_title = chapter["title"]
            ch_text = chapter["text"][:6000]  # Respect context bounds

            # Format current working memory summary (last 4 heuristics + key terms)
            mem_summary = ""
            if working_memory["active_heuristics"]:
                recent_h = working_memory["active_heuristics"][-4:]
                mem_lines = [f"- {h['prioritize']} over {h['over']} (from {h['chapter']})" for h in recent_h]
                mem_summary = "### Previously Established Heuristics:\n" + "\n".join(mem_lines) + "\n"
            if working_memory["cross_references"]:
                mem_summary += "### Known Synergies/Cross-References:\n" + "\n".join(f"- {xr}" for xr in working_memory["cross_references"][-3:])

            prompt = (
                f"You are a cognitive compiler mining directional heuristics from '{self.title}' by {self.author}.\n"
                f"Author Core Worldview: {blueprint.get('core_worldview', '')}\n\n"
                f"{mem_summary}\n\n"
                f"### Current Chapter {idx+1}: {ch_title}\n"
                f"{ch_text}\n\n"
                f"Extract the primary asymmetric decision rule from this chapter. "
                f"Take into account any concepts built up in earlier chapters.\n"
                f"Return a JSON object with:\n"
                f"1. 'prioritize': What action/posture to prioritize (concise phrase)\n"
                f"2. 'over': What tempting alternative or default behavior to sacrifice/deprioritize\n"
                f"3. 'because': The causal mechanism/rationale\n"
                f"4. 'when': The specific triggering context\n"
                f"5. 'boundary_flip_condition': When does this rule INVERT or become dangerous? (The Reversal / exception)\n"
                f"6. 'cross_reference': Does this chapter build on, reinforce, or modify an earlier concept? (string or null)\n\n"
                f"Return ONLY valid JSON."
            )

            resp = call_agent_raw(prompt)
            try:
                m = re.search(r"\{.*\}", resp, re.DOTALL)
                if m:
                    data = json.loads(m.group(0))
                    h_entry = {
                        "chapter": ch_title,
                        "prioritize": data.get("prioritize", ""),
                        "over": data.get("over", ""),
                        "because": data.get("because", ""),
                        "when": data.get("when", ""),
                        "reversal": data.get("boundary_flip_condition", ""),
                    }
                    extracted_heuristics.append(h_entry)
                    working_memory["active_heuristics"].append(h_entry)
                    xr = data.get("cross_reference")
                    if xr:
                        working_memory["cross_references"].append(f"[{ch_title}]: {xr}")
                    print(f"    • [{idx+1}/{len(chapters)}] Extracted: Prioritize {h_entry['prioritize'][:30]}... over {h_entry['over'][:25]}...")
            except Exception as e:
                print(f"    ! Error on chapter {ch_title}: {e}")

        return {
            "heuristics": extracted_heuristics,
            "working_memory": working_memory,
        }

    def _pass3_synthesis(self, blueprint: dict[str, Any], walk_results: dict[str, Any]) -> dict[str, Any]:
        """Pass 3: Synthesizes, clusters, and renders the canonical Cognitive Framework note."""
        all_h = walk_results["heuristics"]
        all_xr = walk_results["working_memory"]["cross_references"]

        prompt = (
            f"You are the master cognitive compiler synthesizing '{self.title}' by {self.author} into a definitive framework.\n"
            f"Worldview: {blueprint.get('core_worldview')}\n\n"
            f"Candidate heuristics extracted across chapters:\n"
            f"{json.dumps(all_h, indent=2)}\n\n"
            f"Cross-chapter links & dependencies:\n"
            f"{json.dumps(all_xr, indent=2)}\n\n"
            f"Select the top 6 to 8 most foundational, non-redundant directional heuristics that define this author's pure taste. "
            f"Resolve any apparent contradictions into contextual flips or prerequisites.\n"
            f"Return a JSON object conforming to the cognitive framework schema:\n"
            f"- 'framework_name': '{self.title}'\n"
            f"- 'slug': '{re.sub(r'[^a-z0-9]+', '-', self.title.lower()).strip('-')}'\n"
            f"- 'source': {{'title': '{self.title}', 'author': '{self.author}', 'kind': 'book', 'url': 'calibre://library'}}\n"
            f"- 'ontology': {{'domain': '{blueprint.get('domain', self.domain)}', 'primitives': {json.dumps(blueprint.get('primitives', []))}}}\n"
            f"- 'core_idea': string\n"
            f"- 'directional_heuristics': array of 6-8 objects with [context, prioritize, over, because, operational_rule, boundary_flip_condition]\n"
            f"- 'boundary_flip_condition': string (when the overall framework should be discarded)\n"
            f"- 'evaluation_rubric': {{'rubric_dimensions': ['accuracy', 'restraint', 'reversibility_awareness']}}\n"
            f"- 'applied_layer': {{'linked_interests': ['strategy', 'decision-making'], 'tier': 2}}\n\n"
            f"Return ONLY valid JSON."
        )

        resp = call_agent_raw(prompt)
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            framework_dict = json.loads(m.group(0))
            framework_dict["schema_version"] = "1.0.0"
            return framework_dict
        return {
            "schema_version": "1.0.0",
            "framework_name": self.title,
            "slug": re.sub(r'[^a-z0-9]+', '-', self.title.lower()).strip('-'),
            "core_idea": blueprint.get("core_worldview", ""),
            "directional_heuristics": all_h[:6],
        }
