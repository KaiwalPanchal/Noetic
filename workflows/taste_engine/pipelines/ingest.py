"""ingest: source (vault note, URL, or book title) → cognitive framework (+ source note).

2-step cached pipeline:
- Step 1: extract: Calls Step 1 using prompts/extract.md and schemas/extraction.json. Tool access is tools=[] [R1].
  Cache key incorporates: source_hash, prompt_hash, schema_version, and model_name [R1].
  If rejected: true, logs reason cleanly and aborts or records rejection.
- Step 2: build_framework: Calls Step 2 using prompts/build_framework.md and schemas/cognitive_framework.json.
  Consumes sanitized Step 1 extraction + vault stances and interests.
- Step 3: write: Applies deduplicate_framework, merges or writes framework note, updates cousin wikilinks,
  updates Master Table, writes source note.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from noetic.knowledge import context, notes
from noetic.knowledge.dedup import deduplicate_framework
from noetic.orchestration.registry import arg, pipeline
from noetic.orchestration.steps import agent_step
from noetic.tools import prompts


@pipeline("ingest", kind="knowledge", help="source → thinking framework (+ source note)",
          args=[arg("source", help="vault note path, URL, or book title")])
def ingest(run, a):
  cfg, src = run.cfg, a["source"]
  web = src.startswith(("http://", "https://"))
  note = None if web else context.resolve_vault_path(cfg, src)
  if web:
    label, body = f"URL: {src}", f"Fetch and read this URL: {src}"
  elif note:
    label, body = f"vault notes: {note.relative_to(cfg.vault).as_posix()}", context.read_body(note, context.BUDGET["note"])
  else:
    label = f"book/topic title: {src}"
    body = f"No notes provided. Related vault excerpts (may be empty):\n{context.search(cfg, src.split(), limit=4)}"

  # Step 1: Extract (Defensive raw cognitive extraction with tools=[]) [R1]
  extract_prompt = prompts.render(cfg, "extract", {"source_label": label, "source": body})

  source_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
  prompt_hash = hashlib.sha256(extract_prompt.encode("utf-8")).hexdigest()[:16]
  schema_ver = getattr(cfg, "schema_version", "1.0.0")
  agent_name = a.get("agent")
  model_name = cfg.model_for("extract", agent_name or "default") or "default"
  extract_cache_key = f"{source_hash}:{prompt_hash}:{schema_ver}:{model_name}"

  extraction = run.step(
    "extract",
    lambda: agent_step(
      run, "extract", "extract", extract_prompt, "extraction",
      agent=a.get("agent"), web=web, tools=[]
    ),
    cache_key=extract_cache_key,
  )

  # If rejected: true, logs reason cleanly and aborts or records rejection
  if extraction.get("rejected"):
    reason = extraction.get("rejection_reason") or "Source flagged as rejected by extraction gate."
    print(f"  ✗ Ingest rejected: {reason}")
    run.state["rejection_reason"] = reason
    run.finish("rejected")
    return []

  # Step 2: Build Framework (Consumes sanitized Step 1 extraction + vault stances and interests)
  build_prompt = prompts.render(
    cfg, "build_framework",
    {
      "extraction": json.dumps(extraction, indent=2, ensure_ascii=False),
      "existing_frameworks": context.frameworks(cfg),
    }
  )
  extract_data_hash = hashlib.sha256(json.dumps(extraction, sort_keys=True).encode("utf-8")).hexdigest()[:16]
  build_prompt_hash = hashlib.sha256(build_prompt.encode("utf-8")).hexdigest()[:16]
  build_model_name = cfg.model_for("build_framework", agent_name or "default") or "default"
  build_cache_key = f"{extract_data_hash}:{build_prompt_hash}:{schema_ver}:{build_model_name}"

  framework_data = run.step(
    "build_framework",
    lambda: agent_step(
      run, "build_framework", "build_framework", build_prompt, "cognitive_framework",
      agent=a.get("agent"), web=False
    ),
    cache_key=build_cache_key,
  )

  # Step 3: Write & Deduplicate
  def write():
    agent = run.agent_for("build_framework") or run.agent_for("extract") or "agent"
    dedup = deduplicate_framework(cfg, framework_data)
    action = dedup["action"]

    if action == "MERGE" and dedup.get("target_path"):
      fw = notes.merge_framework(cfg, dedup["target_path"], framework_data, agent, run.id)
    elif action == "COUSIN" and dedup.get("target_slug"):
      cousin_slug = dedup["target_slug"]
      fw = notes.framework(cfg, framework_data, agent, run.id, cousins=[cousin_slug])
      if dedup.get("target_path"):
        notes.add_cousin_wikilink(dedup["target_path"], framework_data.get("slug") or fw.stem)
    else:  # CREATE
      fw = notes.framework(cfg, framework_data, agent, run.id)

    notes.update_master_table(cfg)
    src_note = notes.source_note(cfg, framework_data, fw, agent, run.id)
    return [run.output(fw), run.output(src_note)]

  return run.step("write", write)
