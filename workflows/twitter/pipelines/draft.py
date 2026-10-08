"""draft: curation package or journey entry → thread draft that passes the length check."""

from noetic.knowledge import context, notes
from noetic.orchestration.registry import arg, pipeline
from noetic.orchestration.run import PipelineError
from noetic.orchestration.steps import agent_step
from noetic.tools import prompts
from noetic.tools.tweets import too_long


@pipeline("draft", kind="content", help="note → validated thread draft", args=[arg("note")])
def draft(run, a):
  cfg = run.cfg
  note = context.resolve_vault_path(cfg, a["note"])
  if not note:
    raise PipelineError("NOTE_NOT_FOUND", a["note"])
  prompt = prompts.render(cfg, "draft", {
    "note_path": note.relative_to(cfg.vault).as_posix(), "note": context.read_body(note, context.BUDGET["note"]),
    "voice": context.voice(cfg), "playbooks": context.playbooks(cfg),
  })
  data = run.step("draft", lambda: agent_step(
    run, "draft", "draft", prompt, "thread", agent=a.get("agent"),
    extra_check=lambda d: too_long([t["text"] for t in d["tweets"]], cfg.x_char_limit)))
  out_dir = cfg.twitter / "drafts" if cfg.twitter in note.parents else cfg.engine / "03-pipeline" / "02-drafts"
  return run.step("write", lambda: [run.output(notes.thread(cfg, data, note, out_dir, run.agent_for("draft"), run.id))])
