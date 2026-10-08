"""Tiny JSON-schema checker (no dependencies).

Supports the subset our schemas use: type, properties, required,
additionalProperties: false, items, enum, minItems. Returns a short list of
human-readable errors, which is also what gets fed back to an agent on retry.
"""

from __future__ import annotations

_TYPES = {
  "object": dict,
  "array": list,
  "string": str,
  "integer": int,
  "number": (int, float),
  "boolean": bool,
}


def check(value, schema: dict, path: str = "$", errors: list[str] | None = None, limit: int = 8) -> list[str]:
  errors = [] if errors is None else errors
  if len(errors) >= limit:
    return errors

  expected = schema.get("type")
  if expected:
    py = _TYPES[expected]
    if isinstance(value, bool) and expected in ("integer", "number"):
      errors.append(f"{path}: expected {expected}, got boolean")
      return errors
    if not isinstance(value, py):
      errors.append(f"{path}: expected {expected}, got {type(value).__name__}")
      return errors

  if "enum" in schema and value not in schema["enum"]:
    errors.append(f"{path}: {value!r} not in {schema['enum']}")

  if isinstance(value, dict):
    props = schema.get("properties", {})
    for key in schema.get("required", []):
      if key not in value:
        errors.append(f"{path}: missing '{key}'")
    if schema.get("additionalProperties") is False:
      for key in value:
        if key not in props:
          errors.append(f"{path}: unexpected '{key}'")
    for key, sub in props.items():
      if key in value:
        check(value[key], sub, f"{path}.{key}", errors, limit)

  if isinstance(value, list):
    if len(value) < schema.get("minItems", 0):
      errors.append(f"{path}: needs at least {schema['minItems']} items, got {len(value)}")
    if "items" in schema:
      for i, item in enumerate(value):
        check(item, schema["items"], f"{path}[{i}]", errors, limit)

  return errors[:limit]
