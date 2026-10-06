"""Security and static defense layer for OverMind.

Implements pre-execution policy checks, AST parsing for untrusted Python code,
path isolation to prevent directory traversal and vault escapes, and input sanitization.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
import re


class SecurityViolation(Exception):
  """Raised when an operation violates sandbox or security policies."""

  pass


# Builtins that are blocked whether called or merely referenced (`f = eval`).
FORBIDDEN_AST_CALLS = {
    "eval",
    "exec",
    "__import__",
    "compile",
    "globals",
    "locals",
    "vars",
    "getattr",
    "setattr",
    "delattr",
    "open",
    "breakpoint",
}

# Method names blocked on any receiver. `compile` is deliberately absent here so
# that `re.compile(...)` stays legal; `builtins.compile` is covered by blocking
# `import builtins`.
FORBIDDEN_AST_ATTR_CALLS = {
    "eval",
    "exec",
    "__import__",
    "open",
    "import_module",
}

# Dotted names (after import-alias resolution) that are blocked.
FORBIDDEN_AST_MODULES = {
    "subprocess",
    "os.system",
    "os.popen",
    "os.spawn",
    "os.posix_spawn",
    "shutil.rmtree",
    "pty",
    "socket",
}

# Modules that may not be imported at all.
FORBIDDEN_IMPORTS = {"subprocess", "pty", "socket", "importlib", "ctypes", "builtins"}

# Attributes that give access to interpreter internals (sandbox-escape chains).
FORBIDDEN_DUNDER_ATTRS = {
    "__class__",
    "__bases__",
    "__base__",
    "__mro__",
    "__subclasses__",
    "__globals__",
    "__builtins__",
    "__code__",
    "__closure__",
    "__dict__",
    "__import__",
    "__loader__",
    "__spec__",
}

DELIMITER_MARKERS = ("<!-- taste-engine:start -->", "<!-- taste-engine:end -->")

# Sensitive files that external agents must never read or write directly
SENSITIVE_FILENAMES = {
    ".env",
    ".private-strings",
    "id_rsa",
    "id_ed25519",
    ".git",
    ".githooks",
}


def validate_vault_path(target_path: Path | str, vault_root: Path | str) -> Path:
  """Ensures target_path stays strictly within vault_root and does not escape."""
  root = Path(vault_root).resolve()
  target = Path(target_path)

  # Reject any '..' path segment outright (either separator style), even if it
  # would resolve back inside the vault: there is no legitimate need for one.
  segments = re.split(r"[\\/]+", str(target_path))
  if ".." in segments:
    raise SecurityViolation(
        f"Path traversal blocked: '..' segment not allowed in '{target_path}'"
    )

  resolved_target = (root / target).resolve() if not target.is_absolute() else target.resolve()

  try:
    resolved_target.relative_to(root)
  except ValueError:
    raise SecurityViolation(
        f"Path traversal blocked: '{resolved_target}' escapes vault root '{root}'"
    )

  # Check if accessing sensitive files
  for part in resolved_target.parts:
    if part.lower() in SENSITIVE_FILENAMES:
      raise SecurityViolation(
          f"Access to protected asset '{part}' blocked by policy gate."
      )

  return resolved_target


def _dotted(node: ast.AST, aliases: dict[str, str]) -> str:
  """Best-effort dotted name for Name/Attribute chains, resolving import aliases."""
  parts: list[str] = []
  while isinstance(node, ast.Attribute):
    parts.append(node.attr)
    node = node.value
  if isinstance(node, ast.Name):
    parts.append(aliases.get(node.id, node.id))
    return ".".join(reversed(parts))
  return ""


def validate_python_ast(code: str) -> None:
  """Static analysis on Python source code to block unsafe calls before execution.

  This is a best-effort denylist, not a sandbox: see docs/threat-model.md.
  """
  try:
    tree = ast.parse(code)
  except SyntaxError as e:
    raise SecurityViolation(f"Invalid Python syntax: {e}")

  # Pass 1: resolve import aliases (`import os as o`, `from os import system as s`)
  # and reject forbidden imports.
  aliases: dict[str, str] = {}
  for node in ast.walk(tree):
    if isinstance(node, ast.Import):
      for alias in node.names:
        if alias.name.split(".")[0] in FORBIDDEN_IMPORTS:
          raise SecurityViolation(
              f"Import of dangerous module '{alias.name}' blocked by static defense policy."
          )
        if alias.asname:
          aliases[alias.asname] = alias.name
    elif isinstance(node, ast.ImportFrom):
      module = node.module or ""
      if module.split(".")[0] in FORBIDDEN_IMPORTS:
        raise SecurityViolation(
            f"Import from dangerous module '{module}' blocked by static defense policy."
        )
      for alias in node.names:
        full = f"{module}.{alias.name}"
        if full in FORBIDDEN_AST_MODULES or alias.name in FORBIDDEN_AST_CALLS:
          raise SecurityViolation(
              f"Import of forbidden name '{full}' blocked by static defense policy."
          )
        aliases[alias.asname or alias.name] = full

  # Pass 2: calls, references and interpreter-internals access.
  for node in ast.walk(tree):
    if isinstance(node, ast.Call):
      if isinstance(node.func, ast.Name):
        if node.func.id in FORBIDDEN_AST_CALLS:
          raise SecurityViolation(
              f"Forbidden builtin '{node.func.id}()' blocked by static defense policy."
          )
        resolved = aliases.get(node.func.id, node.func.id)
        if resolved in FORBIDDEN_AST_MODULES:
          raise SecurityViolation(
              f"Forbidden call '{resolved}()' blocked by static defense policy."
          )
      elif isinstance(node.func, ast.Attribute):
        call_sig = _dotted(node.func, aliases) or f"?.{node.func.attr}"
        if call_sig in FORBIDDEN_AST_MODULES or node.func.attr in FORBIDDEN_AST_ATTR_CALLS:
          raise SecurityViolation(
              f"Forbidden call '{call_sig}()' blocked by static defense policy."
          )
    elif isinstance(node, ast.Name):
      if isinstance(node.ctx, ast.Load) and node.id in FORBIDDEN_AST_CALLS:
        raise SecurityViolation(
            f"Forbidden builtin reference '{node.id}' blocked by static defense policy."
        )
    elif isinstance(node, ast.Attribute):
      if node.attr in FORBIDDEN_DUNDER_ATTRS:
        raise SecurityViolation(
            f"Access to interpreter internals '.{node.attr}' blocked by static defense policy."
        )
      dotted = _dotted(node, aliases)
      if dotted in FORBIDDEN_AST_MODULES:
        raise SecurityViolation(
            f"Forbidden reference '{dotted}' blocked by static defense policy."
        )


def sanitize_input(text: str, max_length: int = 100_000) -> str:
  """Sanitizes user or web input to prevent null-byte attacks and buffer exhaustion."""
  if not isinstance(text, str):
    text = str(text)

  # Check length limit
  if len(text) > max_length:
    raise SecurityViolation(
        f"Input exceeds maximum allowed length of {max_length} characters (got {len(text)})."
    )

  # Strip null bytes and control characters
  cleaned = text.replace("\x00", "")

  # Delimiter injection: untrusted text must not carry the markers that fence
  # engine-owned blocks (see install.py BLOCK_RE), or it could close/forge them.
  for marker in DELIMITER_MARKERS:
    if marker in cleaned:
      raise SecurityViolation(
          f"Delimiter injection blocked: input contains reserved marker '{marker}'."
      )

  return cleaned


def is_safe_command(cmd_args: list[str]) -> bool:
  """Validates shell/CLI command arguments before execution."""
  if not cmd_args:
    return False

  # Normalize lower
  joined = " ".join(cmd_args).lower()

  dangerous_patterns = [
      r"\brm\s+-[rf]{1,2}\s+[/~]",
      r"\bdel\b.*[c-z]:",
      r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",  # Fork bomb
      r"\bformat\s+[c-z]:",
      r"\bmkfs\b",
      r"\bshutdown\b",
  ]

  for pat in dangerous_patterns:
    if re.search(pat, joined):
      return False

  return True
