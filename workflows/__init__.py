"""Workflows: self-contained products built from the overmind blocks.

Each subfolder holds workflow.py (exposing register(app, registry)) plus its own
commands/, prompts/, schemas/, templates/ and scripts/. The core (overmind/) never
imports this package by name: overmind.orchestration.loader discovers it.
To add one, copy a folder, rename it, and edit workflow.py.
"""
