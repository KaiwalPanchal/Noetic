"""Vault naming: new names by default, legacy names still work, `noetic migrate` renames them."""

import json

from noetic.knowledge.config import Config, find_vault, load_config
from noetic.knowledge.migrate import migrate


def _legacy_vault(tmp_path):
  v = tmp_path / "v"
  (v / ".taste-engine" / "runs").mkdir(parents=True)
  (v / "taste-engine.config.json").write_text(json.dumps({"owner": "Old"}), encoding="utf-8")
  return v


def test_legacy_vault_still_loads(tmp_path, monkeypatch):
  v = _legacy_vault(tmp_path)
  monkeypatch.setenv("TASTE_ENGINE_VAULT", str(v))
  monkeypatch.delenv("NOETIC_VAULT", raising=False)
  cfg = load_config()
  assert cfg.owner == "Old" and cfg.state_dir == v / ".taste-engine"


def test_migrate_renames_and_is_idempotent(tmp_path):
  v = _legacy_vault(tmp_path)
  assert "would rename" in " ".join(migrate(v, dry_run=True))
  assert (v / "taste-engine.config.json").exists()  # dry run changed nothing
  migrate(v)
  assert (v / "noetic.config.json").is_file() and (v / ".noetic" / "runs").is_dir()
  assert not (v / "taste-engine.config.json").exists() and not (v / ".taste-engine").exists()
  assert migrate(v) == ["nothing to migrate"]
  assert Config(v, {}).state_dir == v / ".noetic"


def test_migrate_skips_when_both_exist(tmp_path):
  v = _legacy_vault(tmp_path)
  (v / ".noetic").mkdir()
  out = migrate(v)
  assert any(a.startswith("SKIP state folder") for a in out)
  assert (v / ".taste-engine").exists()  # nothing was clobbered


def test_new_env_var_wins(tmp_path, monkeypatch):
  v = tmp_path / "n"
  v.mkdir()
  (v / "noetic.config.json").write_text("{}", encoding="utf-8")
  monkeypatch.setenv("NOETIC_VAULT", str(v))
  assert find_vault() == v
