"""Tools layer: agent CLIs as interchangeable instruments.

One adapter function per CLI, all behind `run_agent(...)`. Add a new agent by
writing a function with the same signature and decorating it with @adapter("name").

Every adapter runs its CLI headless, asks for JSON that matches a schema, and
returns an AgentResult. Failures come back as small diagnostic dicts
(12-factor #9) instead of raw stack traces, so they can be logged or fed back
to a model without flooding its context.

Supported: claude (Claude Code), codex (OpenAI Codex CLI), agy (Antigravity),
gemini (Gemini CLI; needs an eligible account or API key).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time


# Retry-worthy for a *different* agent (vs. bad output, which retries the same one).
INFRA_ERRORS = {"CLI_NOT_FOUND", "AUTH_FAILED", "QUOTA_EXCEEDED", "TIMEOUT", "EXIT_NONZERO"}

_QUOTA_RE = re.compile(r"usage limit|rate limit|quota|too many requests|429|credit balance", re.I)
_AUTH_RE = re.compile(r"authenticat|not logged in|login required|IneligibleTier|401|api key", re.I)


@dataclass
class AgentResult:
  agent: str
  ok: bool
  data: dict | None = None
  error: dict | None = None
  seconds: float = 0.0
  cost_usd: float | None = None
  raw_tail: str = field(default="", repr=False)


def _err(agent: str, code: str, detail: str = "", **extra) -> AgentResult:
  detail = re.sub(r"\s+", " ", detail).strip()[-300:]
  return AgentResult(agent, False, error={"status": "error", "agent": agent, "code": code, "detail": detail, **extra})


def _run(cmd: list[str], *, stdin: str | None, cwd: Path, timeout: int) -> subprocess.CompletedProcess:
  env = {**os.environ, "NO_COLOR": "1", "PYTHONIOENCODING": "utf-8"}
  return subprocess.run(
    cmd, input=stdin, cwd=str(cwd), capture_output=True, text=True,
    encoding="utf-8", errors="replace", timeout=timeout, env=env,
  )


def _extract_json(text: str) -> dict | None:
  """Pull the last JSON object out of free text (handles ```json fences)."""
  fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
  candidates = fenced or [text[text.find("{"): text.rfind("}") + 1]] if "{" in text else []
  for chunk in reversed(candidates):
    try:
      value = json.loads(chunk)
      if isinstance(value, dict):
        return value
    except json.JSONDecodeError:
      continue
  return None


def _strip_for_strict(schema: dict) -> dict:
  """Codex strict mode rejects some keywords; our own checker still enforces them."""
  drop = {"$schema", "title", "minItems", "maxItems"}
  if isinstance(schema, dict):
    return {k: _strip_for_strict(v) for k, v in schema.items() if k not in drop}
  if isinstance(schema, list):
    return [_strip_for_strict(v) for v in schema]
  return schema


def _classify_failure(agent: str, proc: subprocess.CompletedProcess) -> AgentResult:
  text = (proc.stderr or "") + "\n" + (proc.stdout or "")
  if _QUOTA_RE.search(text):
    line = next((l for l in text.splitlines() if _QUOTA_RE.search(l)), text)
    return _err(agent, "QUOTA_EXCEEDED", line[:300], suggested_fallback="another agent, or wait for the limit to reset")
  if _AUTH_RE.search(text):
    line = next((l for l in text.splitlines() if _AUTH_RE.search(l)), text)
    return _err(agent, "AUTH_FAILED", line[:300], suggested_fallback="another agent, or log in to this CLI")
  return _err(agent, "EXIT_NONZERO", text, exit_code=proc.returncode)


ADAPTERS: dict = {}


def adapter(name: str):
  """Register an agent CLI. Signature: fn(prompt, schema, cwd, web, write, timeout, model) -> AgentResult."""
  def deco(fn):
    ADAPTERS[name] = fn
    return fn
  return deco


# ── adapters ────────────────────────────────────────────────────────────────

@adapter("claude")
def _claude(prompt, schema, cwd, web, write, timeout, model) -> AgentResult:
  tools = ["Read", "Glob", "Grep"] + (["WebFetch", "WebSearch"] if web else []) + (["Write", "Edit"] if write else [])
  cmd = [
    shutil.which("claude"), "-p", "--output-format", "json",
    "--json-schema", json.dumps(schema),
    "--model", model or "sonnet",
    "--tools", ",".join(tools), "--allowedTools", ",".join(tools),
    # Lean headless run: skip the user's plugins/MCP/skills (cuts cost ~15x).
    "--strict-mcp-config", "--disable-slash-commands", "--setting-sources", "",
    "--no-session-persistence",
  ]
  if write:
    cmd += ["--permission-mode", "acceptEdits"]
  proc = _run(cmd, stdin=prompt, cwd=cwd, timeout=timeout)
  try:
    envelope = json.loads(proc.stdout)
  except json.JSONDecodeError:
    return _classify_failure("claude", proc)
  if envelope.get("is_error") or proc.returncode != 0:
    return _err("claude", "AUTH_FAILED" if _AUTH_RE.search(str(envelope.get("result"))) else "EXIT_NONZERO",
                str(envelope.get("result") or proc.stderr))
  data = envelope.get("structured_output") or _extract_json(envelope.get("result") or "")
  if data is None:
    return _err("claude", "NO_STRUCTURED_OUTPUT", envelope.get("result") or "")
  return AgentResult("claude", True, data=data, cost_usd=envelope.get("total_cost_usd"))


@adapter("codex")
def _codex(prompt, schema, cwd, web, write, timeout, model) -> AgentResult:
  with tempfile.TemporaryDirectory() as tmp:
    schema_file = Path(tmp) / "schema.json"
    out_file = Path(tmp) / "last.txt"
    schema_file.write_text(json.dumps(_strip_for_strict(schema)), encoding="utf-8")
    cmd = [shutil.which("codex")] + (["--search"] if web else []) + [
      "exec", "--skip-git-repo-check",
      "-s", "workspace-write" if write else "read-only",
      "--output-schema", str(schema_file), "-o", str(out_file), "-C", str(cwd),
    ] + (["-m", model] if model else []) + ["-"]
    proc = _run(cmd, stdin=prompt, cwd=cwd, timeout=timeout)
    last = out_file.read_text(encoding="utf-8") if out_file.exists() else ""
  if proc.returncode != 0 and not last:
    return _classify_failure("codex", proc)
  data = _extract_json(last)
  if data is None:
    return _err("codex", "NO_STRUCTURED_OUTPUT", last or proc.stdout)
  return AgentResult("codex", True, data=data)


@adapter("agy")
def _agy(prompt, schema, cwd, web, write, timeout, model) -> AgentResult:
  # agy only takes the prompt as an argument, and Windows caps command lines
  # at ~32K chars, so the real prompt goes in a file the agent reads first.
  tmp_dir = cwd / ".taste-engine" / "tmp"
  tmp_dir.mkdir(parents=True, exist_ok=True)
  stamp = f"{int(time.time() * 1000)}"
  prompt_file = tmp_dir / f"prompt-{stamp}.md"
  schema_file = tmp_dir / f"schema-{stamp}.json"
  prompt_file.write_text(prompt, encoding="utf-8")
  schema_file.write_text(json.dumps(schema), encoding="utf-8")
  short = (
    f"Read the file {prompt_file} in full. It contains your complete task instructions and context. "
    "Follow them exactly and return only the JSON result."
  )
  cmd = [shutil.which("agy"), "-p", short, "--output-format", "json", "--json-schema", str(schema_file),
         "--disable-slash-commands"]
  cmd += ["--dangerously-skip-permissions"] if write else ["--mode", "plan"]
  if model:
    cmd += ["--model", model]
  try:
    proc = _run(cmd, stdin=None, cwd=cwd, timeout=timeout)
  finally:
    prompt_file.unlink(missing_ok=True)
    schema_file.unlink(missing_ok=True)
  try:
    envelope = json.loads(proc.stdout)
  except json.JSONDecodeError:
    return _classify_failure("agy", proc)
  if envelope.get("status") != "SUCCESS":
    detail = str(envelope.get("error") or envelope.get("response") or proc.stderr)
    return _err("agy", "AUTH_FAILED" if _AUTH_RE.search(detail) else "EXIT_NONZERO", detail)
  data = envelope.get("structured_output") or _extract_json(envelope.get("response") or "")
  if data is None:
    return _err("agy", "NO_STRUCTURED_OUTPUT", envelope.get("response") or "")
  # agy sometimes adds bookkeeping keys; keep only what the schema declares.
  props = schema.get("properties")
  if props:
    data = {k: v for k, v in data.items() if k in props}
  return AgentResult("agy", True, data=data)


@adapter("gemini")
def _gemini(prompt, schema, cwd, web, write, timeout, model) -> AgentResult:
  # No schema flag: put the schema in the prompt and validate afterwards.
  full = f"{prompt}\n\nReturn ONLY a JSON object matching this JSON Schema:\n{json.dumps(schema)}"
  cmd = [shutil.which("gemini"), "-p", "", "-o", "json", "--approval-mode", "yolo" if write else "plan"]
  if model:
    cmd += ["-m", model]
  proc = _run(cmd, stdin=full, cwd=cwd, timeout=timeout)
  try:
    envelope = json.loads(proc.stdout[proc.stdout.find("{"):])
  except (json.JSONDecodeError, ValueError):
    return _classify_failure("gemini", proc)
  data = _extract_json(envelope.get("response") or "")
  if data is None:
    return _err("gemini", "NO_STRUCTURED_OUTPUT", envelope.get("response") or "")
  return AgentResult("gemini", True, data=data)


AGENTS = tuple(ADAPTERS)


def available(agent: str) -> bool:
  return agent in ADAPTERS and shutil.which(agent) is not None


def run_agent(
  agent: str, prompt: str, schema: dict, *, cwd: Path,
  web: bool = False, write: bool = False, timeout: int = 900, model: str | None = None,
) -> AgentResult:
  if agent not in ADAPTERS:
    return _err(agent, "UNKNOWN_AGENT", f"choose one of {AGENTS}")
  if not available(agent):
    return _err(agent, "CLI_NOT_FOUND", f"'{agent}' is not on PATH", suggested_fallback="another agent")
  start = time.time()
  try:
    result = ADAPTERS[agent](prompt, schema, cwd, web, write, timeout, model)
  except subprocess.TimeoutExpired:
    result = _err(agent, "TIMEOUT", f"no result after {timeout}s", suggested_fallback="another agent or a longer --timeout")
  except OSError as exc:
    result = _err(agent, "CLI_NOT_FOUND", str(exc))
  result.seconds = round(time.time() - start, 1)
  return result
