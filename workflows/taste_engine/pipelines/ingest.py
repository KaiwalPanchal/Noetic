"""ingest: source (vault note, URL, or book title) → framework note + source note."""

from noetic.knowledge import context, notes
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

  prompt = prompts.render(cfg, "ingest", {"source_label": label, "source": body, "existing_frameworks": context.frameworks(cfg)})
  data = run.step("extract", lambda: agent_step(run, "extract", "ingest", prompt, "framework", agent=a.get("agent"), web=web))

  def write():
    agent = run.agent_for("extract")
    fw = notes.framework(cfg, data, agent, run.id)
    src_note = notes.source_note(cfg, data, fw, agent, run.id)
    return [run.output(fw), run.output(src_note)]
  return run.step("write", write)
