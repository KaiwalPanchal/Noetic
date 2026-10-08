"""taste_engine pipelines: one module per pipeline, imported by workflow.register().

To add one:
  1. Create workflows/taste_engine/pipelines/<name>.py
  2. Write `def fn(run, a) -> list[str]` that composes the blocks:
       noetic.knowledge.context   build the prompt context
       noetic.tools.prompts       render a prompt from workflows/*/prompts/<name>.md
       noetic.orchestration.steps agent_step(...) for each LLM step (schema in workflows/*/schemas/)
       noetic.knowledge.notes     write the results as notes (status: pending_review)
       noetic.gates.*             anything outside the vault (behind the gate)
     Wrap every unit of work in run.step("name", ...) so it can be resumed.
  3. Decorate it: @pipeline("<name>", kind="knowledge|content|code|project", help="...", args=[arg(...)])
  4. Import it in workflows/taste_engine/workflow.py.
  5. Optional: route it in taste-engine.config.json -> "steps": {"<name>": "<agent>"}
     (otherwise the ordered "agents" list applies, then the first installed adapter)

Current pipelines here: ingest (knowledge), curate and research (content), replicate (code).
"""
