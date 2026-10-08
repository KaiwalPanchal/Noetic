"""Taste Engine pipeline CLI. Python owns the flow; agent CLIs are steps.

  python pipeline.py list                                  # pipelines, agents, routing
  python pipeline.py ingest "Make it stick.md"             # vault note, URL, or book title
  python pipeline.py curate "agent memory"
  python pipeline.py research "temporal knowledge graphs" --agent agy
  python pipeline.py draft "<curation or journey note>"
  python pipeline.py journey "Shipped the multi-agent pipeline"
  python pipeline.py replicate steal-like-an-artist https://a.com https://b.com --goal "portfolio hero" [--build ../my-site]
  python pipeline.py approve "<file>" | reject "<file>" --reason "..."
  python pipeline.py status [run-id] | resume <run-id> | doctor

Architecture: overmind/ (orchestration · knowledge · tools · actions · pipelines).
Every output is `status: pending_review`; nothing is ever posted automatically.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
  sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
  sys.stderr.reconfigure(encoding="utf-8")

from overmind.orchestration.cli import main  # noqa: E402

if __name__ == "__main__":
  main()
