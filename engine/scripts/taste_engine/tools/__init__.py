"""Tools layer: reusable instruments that pipelines compose.

- agents.py        agent CLIs behind run_agent(): built-in adapters, plus any CLI via config `commands`
                   (generic argv template); add a coded one with @adapter("name")
- prompts.py       owned prompts (12-factor #2): fill a template from engine/prompts/, load a schema
- schema_check.py  validates agent JSON against engine/schemas/ (12-factor #4)
- links.py         deterministic URL check (catches invented sources)
- clipper.py       stateless web clipper (extracts DOM/articles into signals/notes)

Thinking frameworks (notes in frameworks/) are tools too: pipelines load them
as instructions for an agent (see pipelines/replicate.py).

Add a tool by putting a module here with plain functions, so pipelines can import it.
Keep tools free of control flow: retries, routing and state belong to orchestration.
"""
