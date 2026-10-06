"""Tools layer: tweet length, weighted the way X counts it.

Every URL counts as 23 characters; emoji and CJK count as 2.
"""

from __future__ import annotations

import re

URL_RE = re.compile(r"https?://\S+")
URL_WEIGHT = 23


def weighted_length(text: str) -> int:
  urls = URL_RE.findall(text)
  text = URL_RE.sub("", text)
  length = len(urls) * URL_WEIGHT
  for ch in text:
    cp = ord(ch)
    # X weights most Latin/punctuation as 1 and everything else (CJK, emoji) as 2.
    if cp <= 0x10FF or 0x2000 <= cp <= 0x200D or 0x2010 <= cp <= 0x201F or 0x2032 <= cp <= 0x2037:
      length += 1
    elif 0xFE00 <= cp <= 0xFE0F:  # variation selectors are free
      continue
    else:
      length += 2
  return length


def too_long(texts: list[str], limit: int) -> list[str]:
  """Validation messages for tweets over the limit (fed back to the agent on retry)."""
  return [f"tweet {i} is {weighted_length(t)} chars (max {limit}); shorten it"
          for i, t in enumerate(texts, 1) if weighted_length(t) > limit]
