"""Scrubber module for blinded LLM judge scoring.

Rule 2 of Section 6: Blind the judge by scrubbing vocabulary.
Strip framework names and jargon ('innovation tokens', 'tattoo', 'haircut',
'deep module', 'canary ledger', 'local-first') from outputs before judging.
Otherwise the judge rewards the vocabulary rather than the actual decision.
"""

from __future__ import annotations

import re

VOCABULARY_SCRUB_PATTERNS = [
    (r"\b[Ii]nnovation\s+[Tt]okens?\b", "technical novelty budget"),
    (r"\b[Tt]attoos?\b", "high-friction irreversible commitment"),
    (r"\b[Hh]aircuts?\b", "moderate-switching decision"),
    (r"\b[Hh]ats?\b", "low-friction reversible choice"),
    (r"\b[Dd]eep\s+[Mm]odules?\b", "compact interface module"),
    (r"\b[Ss]hallow\s+[Mm]odules?\b", "wide interface wrapper"),
    (r"\b[Bb]oring\s+[Tt]echnology\b", "established infrastructure"),
    (r"\b[Ll]ocal-[Ff]irst\b", "device-primary offline architecture"),
    (r"\b[Cc]anary\s+[Ll]edger\b", "append-only transaction pattern"),
    (r"\b[Mm]odular\s+[Tt]ypographic\s+[Ss]cales?\b", "geometric layout sizing"),
    (r"\b[Cc]hoose\s+[Bb]oring\s+[Tt]echnology\b", "standard architecture guidelines"),
    (r"\bDan\s+McKinley\b", "an industry architect"),
    (r"\bJohn\s+Ousterhout\b", "a computer scientist"),
    (r"\bRobert\s+C\.?\s+Martin\b", "a software author"),
    (r"\bInk\s*&\s*Switch\b", "a research lab"),
]


def scrub_vocabulary(text: str) -> str:
    """Replaces distinctive framework jargon with neutral domain descriptions."""
    scrubbed = text
    for pattern, replacement in VOCABULARY_SCRUB_PATTERNS:
        scrubbed = re.sub(pattern, replacement, scrubbed)
    return scrubbed
