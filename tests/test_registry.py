"""Project/quest registry over a temp vault. The private profile is never read."""

from datetime import date

import pytest

from noetic.knowledge import registry
from noetic.gates.policy_gate import SecurityViolation, validate_overmind_path

from .conftest import TODAY

D = date.fromisoformat(TODAY)


def by_name(rows):
  return {r["name"]: r for r in rows}


def test_load_projects_parses_frontmatter_and_staleness(ocfg):
  p = by_name(registry.load_projects(ocfg, today=D))
  a = p["Alpha"]
  assert a["status"] == "active" and a["goal"] == "G1" and a["competency"] == "C1"
  assert a["last_touched"] == "2026-09-01" and a["stale_days"] == 36
  assert a["gate"] == "needs review before release" and a["incomplete"] is False
  assert p["Delta"]["stale_days"] == 2 and p["Delta"]["gate"] == ""


def test_incomplete_projects_report_missing_keys_instead_of_failing(ocfg):
  g = by_name(registry.load_projects(ocfg, today=D))["Gamma"]
  assert g["incomplete"] is True
  assert {"goal", "next_action", "last_touched"} <= set(g["missing"])
  assert g["stale_days"] is None


def test_project_without_frontmatter_or_bad_yaml_is_incomplete(ocfg):
  d = ocfg.overmind / "wiki" / "projects"
  (d / "plain.md").write_text("# no frontmatter", encoding="utf-8")
  (d / "bad.md").write_text("---\nname: [unclosed\n---\n", encoding="utf-8")
  p = by_name(registry.load_projects(ocfg, today=D))
  assert p["plain"]["incomplete"] and p["bad"]["incomplete"]


def test_invalid_status_is_incomplete(ocfg):
  (ocfg.overmind / "wiki" / "projects" / "odd.md").write_text(
      "---\nname: Odd\nstatus: dreaming\ngoal: g\nnext_action: n\nlast_touched: 2026-10-01\n---\n", encoding="utf-8")
  assert by_name(registry.load_projects(ocfg, today=D))["Odd"]["incomplete"] is True


def test_quests_frontmatter_body_lines_overdue_and_xp(ocfg):
  q = {r["id"]: r for r in registry.load_quests(ocfg, today=D)}
  assert set(q) == {"QUEST-001", "QUEST-002", "QUEST-003"}  # XP-LEDGER is not a quest
  assert q["QUEST-001"]["overdue"] is True and q["QUEST-001"]["proposed_xp"] == 50
  assert q["QUEST-002"]["overdue"] is False  # done
  assert q["QUEST-003"]["status"] == "open" and q["QUEST-003"]["due"] == "2026-12-01"
  assert q["QUEST-003"]["overdue"] is False


def test_log_tail_uses_latest_file_and_limits(ocfg):
  assert registry.log_tail(ocfg, lines=5) == [f"entry {i}" for i in range(25, 30)]


def test_no_overmind_configured_gives_empty(cfg):
  assert registry.load_projects(cfg) == [] and registry.load_quests(cfg) == [] and registry.log_tail(cfg) == []


def test_profile_directory_is_never_read(ocfg):
  secret = ocfg.overmind / "wiki" / "profile" / "secret.md"
  with pytest.raises(SecurityViolation):
    registry.read_page(ocfg, secret)
  with pytest.raises(SecurityViolation):
    validate_overmind_path(str(secret), ocfg.vault, ocfg.overmind)
  blob = repr((registry.load_projects(ocfg, today=D), registry.load_quests(ocfg, today=D), registry.log_tail(ocfg)))
  assert "SECRET-PROFILE-TOKEN" not in blob


def test_traversal_and_escape_blocked_and_normal_path_allowed(ocfg):
  with pytest.raises(SecurityViolation):
    validate_overmind_path("OverMind/wiki/projects/../profile/secret.md", ocfg.vault, ocfg.overmind)
  with pytest.raises(SecurityViolation):
    validate_overmind_path(ocfg.vault.parent / "elsewhere.md", ocfg.vault, ocfg.overmind)
  ok = validate_overmind_path("OverMind/wiki/projects/alpha.md", ocfg.vault, ocfg.overmind)
  assert ok.name == "alpha.md"


def test_private_paths_config_also_respected(ocfg):
  ocfg.private_paths = ["OverMind/wiki/projects"]
  assert registry.load_projects(ocfg, today=D) == []
