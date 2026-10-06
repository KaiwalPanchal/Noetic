"""Actions layer: effects outside the pipeline's own notes (12-factor #7).

- gate.py  the human gate: approve / reject a generated note (status in frontmatter)
- git.py   work in other repos: clean-tree check, new branch. Never commits or pushes.

Rules for anything added here:
1. Every public or irreversible action requires the note to be `status: approved` first
   (check with gate.require_approved).
2. Default to the reversible version (a branch, not a commit; a file to copy, not a post).
3. Posting to X stays manual. The owner decided this; don't add an auto-poster without asking.
"""
