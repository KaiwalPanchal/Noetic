import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
  spec = importlib.util.spec_from_file_location("aligner_tool", ROOT / "tools" / "aligner.py")
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  return mod


def test_aligner_reads_architect_contract():
  name, text = _load().load_agent_contract(ROOT)
  assert name == "architect" and "Taxonomy Lock" in text


def test_aligner_falls_back_to_legacy_goal_aligner_name(tmp_path):
  mod = _load()
  (tmp_path / "engine" / "agents").mkdir(parents=True)
  (tmp_path / "engine" / "agents" / "goal_aligner.md").write_text("legacy", encoding="utf-8")
  assert mod.load_agent_contract(tmp_path) == ("goal_aligner", "legacy")
  assert mod.load_agent_contract(tmp_path / "nowhere") == (None, "")
