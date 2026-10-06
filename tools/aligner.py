"""OverMind Goal Aligner & Architectural Audit Tool.

Verifies that the codebase and connected vault adhere to OverMind's 4 primitives:
  1. PROJECTS (Where intent lives: active goals, briefs, domain projects)
  2. KNOWLEDGE BASE (Ground truth on disk: markdown notes, taste graph, frameworks)
  3. TOOLS (Pure stateless instruments: adapters, checkers, scrapers, webclipper)
  4. AGENTS (Autonomous intelligences executing pipelines with human-gated reviews)

Run:
  python tools/aligner.py [--vault "/path/to/vault"]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent

class AlignmentIssue:
    def __init__(self, block: str, severity: str, summary: str, details: str, remediation: str):
        self.block = block          # "PROJECTS" | "KNOWLEDGE" | "TOOLS" | "ACTIONS" | "HARNESS" | "GOVERNANCE"
        self.severity = severity    # "FAIL" | "WARN" | "INFO"
        self.summary = summary
        self.details = details
        self.remediation = remediation

    def __str__(self) -> str:
        symbol = "[FAIL]" if self.severity == "FAIL" else ("[WARN]" if self.severity == "WARN" else "[INFO]")
        return f"{symbol} [{self.block}] {self.summary}\n    Problem: {self.details}\n    Fix: {self.remediation}"


def audit_core_harness_pollution(repo_root: Path) -> list[AlignmentIssue]:
    """Verify that project-specific logic (e.g. Twitter) does not pollute the core engine."""
    issues = []
    
    # Check for gitignored ghost files in engine/
    engine_dir = repo_root / "engine"
    gitignore_path = repo_root / ".gitignore"
    if gitignore_path.exists():
        gi_text = gitignore_path.read_text(encoding="utf-8")
        if "engine/commands/draft.md" in gi_text or "taste_engine/pipelines/draft.py" in gi_text:
            issues.append(AlignmentIssue(
                block="HARNESS",
                severity="FAIL",
                summary="Project files (Twitter) are ghosted in core engine via .gitignore",
                details=(
                    "Twitter-specific commands (/draft, /ship, /journey), pipelines, and schemas "
                    "are gitignored in place inside engine/ rather than modularized into a clean projects/ folder."
                ),
                remediation=(
                    "Move Twitter-specific files into projects/twitter/ (or an isolated project package) "
                    "so the core engine remains a pure framework."
                )
            ))

    # Check config.py defaults
    config_py = repo_root / "engine" / "scripts" / "taste_engine" / "knowledge" / "config.py"
    if config_py.exists():
        cfg_content = config_py.read_text(encoding="utf-8")
        defaults_match = re.search(r"DEFAULTS = \{(.*?)\}", cfg_content, re.S)
        if defaults_match and ("x_char_limit" in defaults_match.group(1) or '"twitter"' in defaults_match.group(1)):
            issues.append(AlignmentIssue(
                block="HARNESS",
                severity="WARN",
                summary="Core config defaults hardcode Twitter domain concepts",
                details="config.py DEFAULTS contains hardcoded keys for 'x_char_limit' or 'twitter' path.",
                remediation="Keep DEFAULTS pure; handle domain project keys in project configs."
            ))

    # Check install.py
    install_py = repo_root / "install.py"
    if install_py.exists():
        inst_text = install_py.read_text(encoding="utf-8")
        if "install_project" not in inst_text and ("twitter-dir" in inst_text or '"twitter"' in inst_text):
            issues.append(AlignmentIssue(
                block="HARNESS",
                severity="WARN",
                summary="Installer explicitly hardcodes Twitter project directory",
                details="install.py creates Twitter directories directly as part of core engine installation.",
                remediation="Decouple project installation: core installs the harness; project packs install their own folders."
            ))

    return issues


def audit_tools_purity(repo_root: Path) -> list[AlignmentIssue]:
    """Verify that tools in taste_engine/tools/ are stateless pure functions and audit Web Clipper."""
    issues = []
    tools_dir = repo_root / "engine" / "scripts" / "taste_engine" / "tools"
    
    # Check Web Clipper tool status
    clipper_tool = tools_dir / "clipper.py"
    if not clipper_tool.exists():
        issues.append(AlignmentIssue(
            block="TOOLS",
            severity="FAIL",
            summary="Web Clipper is not implemented as a Tool in taste_engine/tools/",
            details=(
                "User requirement designates Web Clipper as a Tool. "
                "However, no clipper.py exists in taste_engine/tools/. "
                "Instead, docs speculate an external 'modules/clipper/' that does not exist."
            ),
            remediation=(
                "Implement taste_engine/tools/clipper.py as a clean, stateless Tool "
                "(functions: clip_url, parse_html, format_signal) feeding markdown directly into Knowledge Base."
            )
        ))

    # Check for project tools misplaced in core tools
    tweets_tool = tools_dir / "tweets.py"
    if tweets_tool.exists():
        issues.append(AlignmentIssue(
            block="TOOLS",
            severity="WARN",
            summary="tweets.py is a project tool located in the core tools folder",
            details="tweets.py handles Twitter character weighting, which belongs to the Twitter project.",
            remediation="Package tweets.py alongside the Twitter project or as an optional domain validator."
        ))

    return issues


def audit_speculative_architecture(repo_root: Path) -> list[AlignmentIssue]:
    """Verify that documentation does not describe non-existent architectures."""
    issues = []
    readme = repo_root / "README.md"
    arch = repo_root / "ARCHITECTURE.md"

    for doc in [readme, arch]:
        if doc.exists():
            text = doc.read_text(encoding="utf-8")
            if "modules/clipper/" in text or "overmind-clipper" in text:
                modules_dir = repo_root / "modules"
                if not modules_dir.exists():
                    issues.append(AlignmentIssue(
                        block="KNOWLEDGE",
                        severity="WARN",
                        summary=f"Speculative architecture documented in {doc.name}",
                        details=(
                            f"{doc.name} describes 'modules/clipper/' with MongoDB Atlas and webhooks, "
                            "but the 'modules/' directory does not exist in the repository."
                        ),
                        remediation=(
                            "Reconcile documentation with reality: either implement the Web Clipper as a clean Tool "
                            "in tools/ or build the modules/ directory if modular architecture is intended."
                        )
                    ))
                    break
    return issues


def audit_vault_alignment(vault_root: Path) -> list[AlignmentIssue]:
    """Verify that the vault adheres to OverMind governance and projects structure."""
    issues = []
    overmind_dir = vault_root / "OverMind"
    if not overmind_dir.exists():
        issues.append(AlignmentIssue(
            block="GOVERNANCE",
            severity="WARN",
            summary="OverMind governance directory missing in vault",
            details=f"No OverMind directory found at {vault_root}",
            remediation="Ensure vault has OverMind/ structure."
        ))
        return issues

    projects_wiki = overmind_dir / "wiki" / "projects"
    twitter_dir = vault_root / "Twitter"
    
    # Check if Twitter exists in vault but lacks a formal project wiki note
    if twitter_dir.exists():
        twitter_proj_note = projects_wiki / "twitter-build-in-public.md"
        legacy_twitter_note = projects_wiki / "twitter.md"
        if not twitter_proj_note.exists() and not legacy_twitter_note.exists():
            issues.append(AlignmentIssue(
                block="PROJECTS",
                severity="FAIL",
                summary="Twitter folder exists in vault but lacks a Project note in OverMind/wiki/projects/",
                details=(
                    "User states 'twitter thing is basically a project here'. "
                    "However, wiki/projects/ only has taste-engine.md, overmind-as-product.md, and active project notes. "
                    "Twitter is not formally tracked as an active Project with deliverables, metrics, and quests."
                ),
                remediation=(
                    "Create OverMind/wiki/projects/twitter-build-in-public.md linking to Goal G7 & Competency C2, "
                    "formalizing its scope, cadence (Tue/Fri), and next action."
                )
            ))

    # Check for loose files in vault root that should be classified
    root_loose_candidates = [
        "Taste Engine — Guide & Status.md",
        "building systems that evolve and scale in age of AI..md",
    ]
    for loose_name in root_loose_candidates:
        if (vault_root / loose_name).exists():
            issues.append(AlignmentIssue(
                block="KNOWLEDGE",
                severity="INFO",
                summary=f"Unclassified note at vault root: {loose_name}",
                details=f"'{loose_name}' sits at vault root instead of an architectural folder.",
                remediation="Move to appropriate folder (e.g. Applied AI/02-signals/, frameworks/, or project docs)."
            ))

    # Anti-abandonment check: verify thread-001 vs open quests
    draft_thread = vault_root / "Applied AI" / "03-pipeline" / "02-drafts" / "thread-001-why-agent-memory-is-broken.md"
    xp_ledger = overmind_dir / "wiki" / "quests" / "XP-LEDGER.md"
    if draft_thread.exists() and xp_ledger.exists():
        xp_text = xp_ledger.read_text(encoding="utf-8")
        if "QUEST-002" not in xp_text:
            issues.append(AlignmentIssue(
                block="GOVERNANCE",
                severity="WARN",
                summary="Anti-Abandonment Alert: thread-001 is drafted but unposted, blocking QUEST-002",
                details=(
                    "QUEST-002 gate requires publishing thread-001. "
                    "Building further meta-tooling before publishing violates OverMind's anti-abandonment guardrail."
                ),
                remediation="Ship and post thread-001 by hand to close QUEST-002 before expanding engine features."
            ))

    return issues


def run_audit(repo_root: Path, vault_root: Path | None) -> list[AlignmentIssue]:
    all_issues = []
    all_issues.extend(audit_core_harness_pollution(repo_root))
    all_issues.extend(audit_tools_purity(repo_root))
    all_issues.extend(audit_speculative_architecture(repo_root))
    if vault_root and vault_root.is_dir():
        all_issues.extend(audit_vault_alignment(vault_root))
    return all_issues


def main():
    parser = argparse.ArgumentParser(description="OverMind Goal Aligner & Architectural Audit")
    parser.add_argument("--repo", default=str(REPO_ROOT), help="Path to OverMind engine repository")
    parser.add_argument("--vault", help="Path to OverMind/Obsidian vault (optional)")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    vault = Path(args.vault).resolve() if args.vault else None

    # If vault not passed, check env or discover sibling folder with taste-engine.config.json
    if not vault:
        import os
        env_vault = os.environ.get("TASTE_ENGINE_VAULT")
        if env_vault and Path(env_vault).is_dir():
            vault = Path(env_vault)
        else:
            for parent in [repo.parent, repo.parent.parent]:
                try:
                    for candidate in parent.glob("*"):
                        if candidate.is_dir() and (candidate / "taste-engine.config.json").is_file():
                            vault = candidate
                            break
                except Exception:
                    pass
                if vault:
                    break

    print("=" * 70)
    print(" OVERMIND GOAL ALIGNER — ARCHITECTURAL AUDIT")
    print("=" * 70)
    print(f"Engine Repo: {repo}")
    print(f"Vault:       {vault or 'Not specified'}\n")

    issues = run_audit(repo, vault)

    fails = [i for i in issues if i.severity == "FAIL"]
    warns = [i for i in issues if i.severity == "WARN"]
    infos = [i for i in issues if i.severity == "INFO"]

    print(f"Audit Summary: {len(fails)} FAIL, {len(warns)} WARN, {len(infos)} INFO\n")

    for i in issues:
        print(i)
        print("-" * 70)

    if fails:
        print("\n[RESULT] Alignment status: NOT UNIFIED (Structural remediation required).")
        return 1
    elif warns:
        print("\n[RESULT] Alignment status: MOSTLY ALIGNED (Warnings to address).")
        return 0
    else:
        print("\n[RESULT] Alignment status: FULLY ALIGNED AND UNIFIED.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
