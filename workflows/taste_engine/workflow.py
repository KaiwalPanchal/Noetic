"""taste_engine workflow: registers the ingest / curate / research / replicate pipelines.

Its canonical commands (apply, curate, ingest, research) live in commands/ and reach each agent
through the generated adapters; its prompts, schemas and templates sit beside this file.
"""

from __future__ import annotations


def register(app, registry):
  """Importing the pipeline modules runs their @pipeline decorators against the shared registry."""
  from workflows.taste_engine.pipelines import curate, ingest, replicate, research  # noqa: F401
