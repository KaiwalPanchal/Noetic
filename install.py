"""Thin wrapper kept for `python install.py --vault ...` from a checkout. Real code: overmind/installer.py."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from overmind.installer import main  # noqa: E402

if __name__ == "__main__":
  main()
