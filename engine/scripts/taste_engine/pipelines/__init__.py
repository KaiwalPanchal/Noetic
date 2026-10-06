"""Pipelines: one module per pipeline, auto-discovered by the CLI.

To add one:
  1. Create taste_engine/pipelines/<name>.py
  2. Write `def fn(run, a) -> list[str]` that composes the layers:
       knowledge.context   → build the prompt context
       tools.prompts       → render a prompt from engine/prompts/<name>.md
       orchestration.steps → agent_step(...) for each LLM step (schema in engine/schemas/)
       knowledge.notes     → write the results as notes (status: pending_review)
       actions.*           → anything outside the vault (behind the gate)
     Wrap every unit of work in run.step("name", ...) so it can be resumed.
  3. Decorate it: @pipeline("<name>", kind="knowledge|content|code|project", help="...", args=[arg(...)])
  4. Optional: route it to an agent in taste-engine.config.json → "agents": {"<name>": "claude"}

Current pipelines
  knowledge: ingest
  content:   curate, research, draft, journey
  code:      replicate
"""
