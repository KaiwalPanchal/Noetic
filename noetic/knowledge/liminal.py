"""Knowledge layer: optional Liminal sidecar HTTP client (stdlib only).

Connects to a running Liminal graph-RAG service for grounded memory recall
and inbox document ingestion. Operates strictly as a sidecar; Noetic remains
fully functional when Liminal is absent or disabled.
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any

from noetic.knowledge.config import Config


class LiminalError(Exception):
  """Raised when an error occurs while communicating with the Liminal sidecar."""


class LiminalClient:
  def __init__(self, base_url: str, timeout: int = 10):
    self.base_url = base_url.rstrip("/")
    self.timeout = timeout

  def _request(self, method: str, path: str, payload: dict | None = None) -> dict[str, Any]:
    url = f"{self.base_url}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
      with urllib.request.urlopen(req, timeout=self.timeout) as resp:
        if resp.status < 200 or resp.status >= 300:
          raise LiminalError(f"Liminal returned HTTP {resp.status} for {path}")
        raw = resp.read()
    except urllib.error.HTTPError as exc:
      raise LiminalError(f"Liminal HTTP {exc.code} for {path}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
      raise LiminalError(f"Liminal unreachable at {url}: {exc.reason}") from exc
    except (TimeoutError, socket.timeout) as exc:
      raise LiminalError(f"Liminal request timed out after {self.timeout}s for {path}") from exc
    except LiminalError:
      raise
    except Exception as exc:
      raise LiminalError(f"Liminal request failed for {path}: {exc}") from exc

    try:
      return json.loads(raw.decode("utf-8"))
    except Exception as exc:
      raise LiminalError(f"Liminal returned malformed JSON for {path}: {exc}") from exc

  def health(self) -> dict[str, Any]:
    """Check health and neo4j status of Liminal backend."""
    return self._request("GET", "/health")

  def query(
      self,
      question: str,
      *,
      max_hops: int = 2,
      top_k: int = 5,
      filter_by_goal: str | None = None,
  ) -> dict[str, Any]:
    """Execute a grounded graph-RAG query against Liminal."""
    payload = {
      "query": question,
      "max_hops": max_hops,
      "top_k": top_k,
      "filter_by_goal": filter_by_goal,
    }
    return self._request("POST", "/api/query", payload)

  def ingest(
      self,
      title: str,
      content: str,
      *,
      source_type: str = "obsidian",
      tags: list[str] | None = None,
      author: str | None = "noetic",
  ) -> dict[str, Any]:
    """Ingest a markdown document into Liminal's knowledge graph."""
    payload = {
      "content": content,
      "title": title,
      "source_type": source_type,
      "source_url": None,
      "author": author,
      "tags": tags or [],
      "metadata": {},
    }
    return self._request("POST", "/api/ingest/document", payload)


def client_for(cfg: Config) -> LiminalClient | None:
  """Return a LiminalClient if configured in cfg, else None."""
  if not cfg.liminal_url:
    return None
  return LiminalClient(cfg.liminal_url, cfg.liminal_timeout)
