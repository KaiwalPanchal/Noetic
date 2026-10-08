"""Knowledge layer: grounded memory recall with Liminal sidecar and grep fallback.

Queries Liminal graph-RAG service when configured and reachable. If absent,
unreachable, or errored, deterministically falls back to private-aware vault grep.
"""

from __future__ import annotations

import re
from typing import Any

from noetic.knowledge import context
from noetic.knowledge.config import Config
from noetic.knowledge.liminal import LiminalError, client_for


def recall(cfg: Config, question: str) -> dict[str, Any]:
  """Recall grounded context for a question via Liminal or vault-grep fallback."""
  client = client_for(cfg)
  if client is not None:
    try:
      res = client.query(question)
      status = res.get("status", "GROUNDED")
      citations = [
        n.get("entity_name", "") for n in res.get("cited_nodes", [])
        if isinstance(n, dict) and n.get("entity_name")
      ]
      return {
        "source": "liminal",
        "status": status,
        "answer": res.get("answer", ""),
        "citations": citations,
        "note": "",
      }
    except LiminalError as exc:
      note = f"liminal unreachable: {exc}"
  else:
    note = "liminal not configured"

  terms = [w for w in re.findall(r"\w+", question) if len(w) > 3]
  terms = terms or [question]
  answer = context.search(cfg, terms)
  return {
    "source": "vault-grep",
    "status": "UNGROUNDED",
    "answer": answer,
    "citations": [],
    "note": note,
  }
