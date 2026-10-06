"""install.py smoke test: the twitter pack is installed from its canonical package location."""

from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parent.parent


def test_install_into_fresh_vault_includes_twitter_pack(tmp_path: Path):
  vault = tmp_path / "vault"
  vault.mkdir()
  res = subprocess.run([sys.executable, str(REPO / "install.py"), "--vault", str(vault)],
                       capture_output=True, text=True, encoding="utf-8")
  assert res.returncode == 0, res.stderr
  assert (vault / ".claude" / "commands" / "draft.md").is_file()           # pack command
  engine = vault / "taste-engine" / "scripts"
  assert (engine / "taste_engine" / "pipelines" / "draft.py").is_file()     # pack pipeline
  assert (engine / "thread_validator.py").is_file()                         # pack script
  assert not (engine / "__init__.py").exists()                              # markers not leaked
  assert (vault / "Twitter" / "journey").is_dir()
