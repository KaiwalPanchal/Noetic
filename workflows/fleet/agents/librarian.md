---
name: librarian
description: Daily inbox triage. Flags empty/duplicate notes and suggests links. Never moves, edits or deletes.
trigger: schedule:daily
policy: workflow
pipeline: librarian
tools: [scan_inbox]
---
Deterministic. No model is called. Output is a pending_review digest note.
