"""Orchestration layer: the planner (12-factor #8, #6, #12).

- registry.py  pipelines register with @pipeline(...); the CLI is generated from it
- run.py       a Run = one pipeline execution, state saved to .taste-engine/runs/<id>.json;
               finished steps are cached, so `resume` continues where a failure stopped
- steps.py     agent_step(): route to an agent → call → validate → retry with a compact
               error → fall back to the next agent
- cli.py       `python pipeline.py <pipeline|approve|reject|status|resume|doctor|list>`

Control flow is plain Python. LLM calls are isolated steps, never an open-ended loop.
"""
