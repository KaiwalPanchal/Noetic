"""Tests for schema_check validator."""

from noetic.tools.schema_check import check


def test_schema_valid_object():
  schema = {
      "type": "object",
      "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
      "required": ["name", "age"],
      "additionalProperties": False,
  }
  errors = check({"name": "Alice", "age": 30}, schema)
  assert errors == []


def test_schema_missing_required():
  schema = {
      "type": "object",
      "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
      "required": ["name", "age"],
  }
  errors = check({"name": "Alice"}, schema)
  assert len(errors) == 1
  assert "missing 'age'" in errors[0]


def test_schema_type_mismatch():
  schema = {
      "type": "object",
      "properties": {"age": {"type": "integer"}},
      "required": ["age"],
  }
  errors = check({"age": "thirty"}, schema)
  assert len(errors) == 1
  assert "expected integer" in errors[0]


def test_schema_additional_properties_forbidden():
  schema = {
      "type": "object",
      "properties": {"name": {"type": "string"}},
      "required": ["name"],
      "additionalProperties": False,
  }
  errors = check({"name": "Bob", "extra": 123}, schema)
  assert len(errors) == 1
  assert "unexpected 'extra'" in errors[0]


def test_schema_enum_validation():
  schema = {
      "type": "object",
      "properties": {"status": {"type": "string", "enum": ["active", "archived"]}},
      "required": ["status"],
  }
  assert check({"status": "active"}, schema) == []
  errors = check({"status": "pending"}, schema)
  assert len(errors) == 1
  assert "not in" in errors[0]


def test_schema_array_min_items():
  schema = {
      "type": "object",
      "properties": {"tags": {"type": "array", "items": {"type": "string"}, "minItems": 2}},
      "required": ["tags"],
  }
  assert check({"tags": ["a", "b"]}, schema) == []
  errors = check({"tags": ["a"]}, schema)
  assert len(errors) == 1
  assert "needs at least 2 items" in errors[0]
