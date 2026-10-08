"""Gates: where a human or a policy must say yes before anything leaves the pipeline.

- gate.py         the human gate: approve / reject a generated note (status in frontmatter)
- git.py          work in other repos: clean-tree check, new branch. Never commits or pushes.
- policy_gate.py  static defense: vault path confinement, AST check of generated code, input sanitising

Rules for anything added here:
1. Every public or irreversible action requires the note to be `status: approved` first
   (check with gate.require_approved).
2. Default to the reversible version (a branch, not a commit; a file to copy, not a post).
3. Posting to X stays manual. The owner decided this; don't add an auto-poster without asking.
"""

from noetic.gates.policy_gate import (
    SecurityViolation,
    is_safe_command,
    sanitize_input,
    validate_python_ast,
    validate_vault_path,
)

__all__ = ["SecurityViolation", "validate_vault_path", "validate_python_ast", "sanitize_input", "is_safe_command"]
