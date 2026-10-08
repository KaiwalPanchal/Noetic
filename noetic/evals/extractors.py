"""Pluggable extractors for the eval harness.

An extractor is any callable ``(source_text: str) -> dict`` returning:

    {"title": str, "core_principles": [str], "mental_moves": [str],
     "anti_patterns": [str], "rejected": bool}

It deliberately receives ONLY the source text (no category, no label), so it
cannot peek at the answer. To evaluate a real LLM-backed extractor, write a
callable with that signature and pass ``--extractor your_module:your_callable``
(see ``load_extractor``).

Shipped here: ``RuleBasedExtractor``, a deterministic, zero-cost baseline. Its
rules were written after reading this golden set, so its score is in-sample and
says nothing about generalization. It exists to give the harness a
non-circular, reproducible number to regress against, and as a floor any real
extractor should beat.
"""

from __future__ import annotations

import importlib
import re
from typing import Callable

Extractor = Callable[[str], dict]

_INJECTION_PATTERNS = [
    r"ignore (all )?(prior|previous|above)",
    r"disregard (the |all |any )?(json |schema|rules|instructions|prior)",
    r"emergency override",
    r"\boverride\b.{0,40}\b(true|constraints|safety)",
    r"you are now acting as",
    r"\bdan mode\b",
    r"delete all",
    r"grant admin",
    r"private keys?",
    r"system prompt",
    r"taste-engine:(start|end)",
    r"(run|execute) (the|this) (command|decoded|payload)",
    r"output the word",
    r"\b[A-Za-z0-9+/]{32,}={0,2}(?![A-Za-z0-9+/])",  # long base64-looking blob
]

_FLUFF_TERMS = [
    "synerg", "paradigm", "disrupt", "holistic", "next-gen", "game-chang",
    "hyper-scal", "seamless", "unlock", "leverag", "ecosystem", "cannot afford",
    "drop a like", "cheat sheet", "revolutioniz", "cutting-edge",
]

_MOVE_CUES = re.compile(
    r"\b(because|so that|trade|guarantee|regardless|unless|whereas|instead|enables?|"
    r"records?|returns?)\b", re.I)
_ANTI_CUES = re.compile(r"\b(not|without|only|weak|blocks?|never|fails?|cannot)\b", re.I)


def _sentences(text: str) -> list[str]:
  parts = re.split(r"(?<=[.!?])\s+", text.strip())
  return [p.strip() for p in parts if len(p.split()) >= 5]


class RuleBasedExtractor:
  """Deterministic extractive baseline. Not an LLM; makes no semantic claims."""

  name = "rule-based-baseline"

  def __call__(self, source_text: str) -> dict:
    lowered = source_text.lower()
    injected = any(re.search(p, source_text, re.I) for p in _INJECTION_PATTERNS)
    fluff_hits = sum(1 for t in _FLUFF_TERMS if t in lowered)
    sentences = _sentences(source_text)
    rejected = injected or fluff_hits >= 2 or not sentences

    if rejected:
      return {"title": "Rejected", "core_principles": [], "mental_moves": [],
              "anti_patterns": [], "rejected": True}

    return {
        "title": " ".join(sentences[0].split()[:8]),
        "core_principles": sentences,
        "mental_moves": [s for s in sentences if _MOVE_CUES.search(s)][:3],
        "anti_patterns": [s for s in sentences if _ANTI_CUES.search(s)][:3],
        "rejected": False,
    }


def load_extractor(spec: str) -> Extractor:
  """Resolve ``package.module:attr`` to an extractor callable.

  If ``attr`` is a class it is instantiated with no arguments.
  """
  if ":" not in spec:
    raise ValueError(f"Extractor spec must look like 'module:callable', got {spec!r}")
  module_name, attr = spec.split(":", 1)
  obj = getattr(importlib.import_module(module_name), attr)
  if isinstance(obj, type):
    obj = obj()
  if not callable(obj):
    raise ValueError(f"{spec!r} is not callable")
  return obj
