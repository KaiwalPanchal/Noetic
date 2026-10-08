"""Tests for Liminal sidecar client, recall, and librarian push."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import pytest

from noetic.knowledge.liminal import LiminalClient, LiminalError, client_for
from noetic.knowledge.recall import recall
from workflows.fleet.librarian import push_to_liminal


class FakeLiminalServer(ThreadingHTTPServer):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.requests_log = []
    self.responses = {}


class FakeLiminalHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    self.server.requests_log.append({"method": "GET", "path": self.path})
    resp = self.server.responses.get(self.path, {"status": 200, "body": {"status": "healthy", "neo4j_connected": True}})
    status = resp.get("status", 200)
    body = resp.get("body", {})
    raw = body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")
    self.send_response(status)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(raw)))
    self.end_headers()
    self.wfile.write(raw)

  def do_POST(self):
    length = int(self.headers.get("Content-Length", 0))
    body_bytes = self.rfile.read(length) if length else b"{}"
    try:
      parsed = json.loads(body_bytes.decode("utf-8"))
    except Exception:
      parsed = {}
    self.server.requests_log.append({"method": "POST", "path": self.path, "data": parsed})
    resp = self.server.responses.get(self.path, {"status": 200, "body": {"status": "ok"}})
    status = resp.get("status", 200)
    body = resp.get("body", {})
    raw = body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")
    self.send_response(status)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(raw)))
    self.end_headers()
    self.wfile.write(raw)

  def log_message(self, format, *args):
    pass


@pytest.fixture
def fake_liminal():
  server = FakeLiminalServer(("127.0.0.1", 0), FakeLiminalHandler)
  port = server.server_address[1]
  t = threading.Thread(target=server.serve_forever, daemon=True)
  t.start()
  server.base_url = f"http://127.0.0.1:{port}"
  yield server
  server.shutdown()
  server.server_close()


def test_health_ok(fake_liminal):
  client = LiminalClient(fake_liminal.base_url)
  fake_liminal.responses["/health"] = {
    "status": 200,
    "body": {"status": "healthy", "neo4j_connected": True},
  }
  res = client.health()
  assert res["status"] == "healthy"
  assert res["neo4j_connected"] is True


def test_query_grounded_mapping(fake_liminal, cfg):
  cfg.liminal_url = fake_liminal.base_url
  fake_liminal.responses["/api/query"] = {
    "status": 200,
    "body": {
      "answer": "Grounded answer from graph.",
      "status": "GROUNDED",
      "confidence_score": 0.95,
      "cited_nodes": [{"node_id": "1", "entity_name": "Node A", "entity_type": "concept"}],
      "cited_passages": ["passage 1"],
    },
  }
  res = recall(cfg, "What is Node A?")
  assert res["source"] == "liminal"
  assert res["status"] == "GROUNDED"
  assert res["answer"] == "Grounded answer from graph."
  assert res["citations"] == ["Node A"]
  assert res["note"] == ""


def test_query_refused_passes_through_without_grep(fake_liminal, cfg, monkeypatch):
  cfg.liminal_url = fake_liminal.base_url
  fake_liminal.responses["/api/query"] = {
    "status": 200,
    "body": {
      "answer": "I do not have enough context.",
      "status": "REFUSED_INSUFFICIENT_CONTEXT",
      "cited_nodes": [],
    },
  }
  called_grep = []
  from noetic.knowledge import context
  monkeypatch.setattr(context, "search", lambda *a: called_grep.append(True) or "manufactured")

  res = recall(cfg, "Unknown topic?")
  assert res["source"] == "liminal"
  assert res["status"] == "REFUSED_INSUFFICIENT_CONTEXT"
  assert res["answer"] == "I do not have enough context."
  assert len(called_grep) == 0


def test_unreachable_port_falls_back_to_grep(cfg):
  cfg.liminal_url = "http://127.0.0.1:59999"
  res = recall(cfg, "arbitrary search query")
  assert res["source"] == "vault-grep"
  assert res["status"] == "UNGROUNDED"
  assert "liminal unreachable" in res["note"]


def test_non_200_raises_liminal_error(fake_liminal):
  fake_liminal.responses["/health"] = {"status": 500, "body": {"error": "internal error"}}
  client = LiminalClient(fake_liminal.base_url)
  with pytest.raises(LiminalError) as exc:
    client.health()
  assert "HTTP 500" in str(exc.value)


def test_unconfigured_client_for_none(cfg):
  cfg.liminal_url = None
  assert client_for(cfg) is None


def test_librarian_push_idempotent_skips_by_hash(fake_liminal, cfg):
  fake_liminal.responses["/api/ingest/document"] = {
    "status": 200,
    "body": {"document_id": "doc_123", "status": "indexed"},
  }
  client = LiminalClient(fake_liminal.base_url)
  inbox = cfg.vault / "inbox"
  inbox.mkdir(parents=True, exist_ok=True)
  (inbox / "note1.md").write_text("# Note 1\nSome meaningful text body", encoding="utf-8")

  # First push
  res1 = push_to_liminal(cfg, client)
  assert res1["pushed"] == 1
  assert res1["skipped"] == 0

  # Second push skips by hash
  res2 = push_to_liminal(cfg, client)
  assert res2["pushed"] == 0
  assert res2["skipped"] == 1


def test_private_note_never_posted(fake_liminal, ocfg):
  ocfg.private_paths = ["Private"]
  inbox = ocfg.vault / "inbox"
  inbox.mkdir(parents=True, exist_ok=True)
  (inbox / "public.md").write_text("# Public Note\nPublic info", encoding="utf-8")

  # Private folder
  priv_dir = ocfg.vault / "Private"
  priv_dir.mkdir(parents=True, exist_ok=True)
  (priv_dir / "secret.md").write_text("CLASSIFIED DATA", encoding="utf-8")

  # Overmind profile note
  prof = ocfg.overmind / "wiki" / "profile"
  prof.mkdir(parents=True, exist_ok=True)
  (prof / "secret_profile.md").write_text("SECRET PROFILE INFO", encoding="utf-8")

  fake_liminal.responses["/api/ingest/document"] = {
    "status": 200,
    "body": {"document_id": "doc_pub", "status": "indexed"},
  }
  client = LiminalClient(fake_liminal.base_url)
  fake_liminal.requests_log.clear()

  push_to_liminal(ocfg, client)

  for req in fake_liminal.requests_log:
    req_body = str(req.get("data", {}))
    assert "CLASSIFIED DATA" not in req_body
    assert "SECRET PROFILE INFO" not in req_body


def test_malformed_json_raises_liminal_error(fake_liminal):
  fake_liminal.responses["/health"] = {"status": 200, "body": "NOT_VALID_JSON{}"}
  client = LiminalClient(fake_liminal.base_url)
  with pytest.raises(LiminalError) as exc:
    client.health()
  assert "malformed JSON" in str(exc.value)
