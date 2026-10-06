"""Taste Engine: an agent framework on top of a markdown second brain.

Four layers. Each one is a place to add things later:

  orchestration/  The planner. Runs pipelines as fixed step sequences, keeps run
                  state on disk (pause/resume), routes agent steps, retries and
                  falls back. New pipelines plug in through its registry.

  knowledge/      The vault: config, context building (what the model is allowed
                  to see), and note writers. Knowledge pipelines (indexing,
                  organizing, linking) read and write here.

  tools/          Reusable instruments: agent CLIs (claude, codex, agy, gemini),
                  prompt rendering, validators (schema, tweet length, link check).
                  New tools and agent adapters go here.

  actions/        Side effects outside the vault: git branches and builds in other
                  repos, and the human gate (approve/reject). Anything public must
                  pass the gate first. The engine never posts on its own.

  pipelines/      One file per pipeline. Each composes the four layers and
                  registers itself with @pipeline(...).

Dependency direction: pipelines → orchestration → (tools, actions) → knowledge.
"""
