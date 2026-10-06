"""Tests for the Typer CLI commands."""

from typer.testing import CliRunner
from taste_engine.cli import app

runner = CliRunner()


def test_cli_help():
  result = runner.invoke(app, ["--help"])
  assert result.exit_code == 0
  assert "OverMind" in result.output
  assert "doctor" in result.output
  assert "mcp" in result.output
  assert "eval" in result.output


def test_cli_eval():
  result = runner.invoke(app, ["eval"])
  assert result.exit_code == 0
  assert "GATE PASSED" in result.output


def test_cli_doctor():
  result = runner.invoke(app, ["doctor"])
  assert result.exit_code == 0
  assert "Model Context Protocol (MCP) Server" in result.output
  assert "Security Policy Gate" in result.output


def test_cli_eval_heldout_is_honestly_below_the_golden_gate():
  # The rule-based baseline was fitted on the golden set; on the held-out set it
  # misses the default 0.80 gate. That is the point of having a held-out set.
  assert runner.invoke(app, ["eval", "-q", "--dataset", "heldout"]).exit_code == 1
  assert runner.invoke(app, ["eval", "-q", "--dataset", "heldout", "--threshold", "0.5"]).exit_code == 0
