"""Pre-commit guard: block private strings from entering the public repo.

Reads a deny-list from `.private-strings` (gitignored, one string per line,
case-insensitive) and scans the staged files. Exits 1 if any appear.
Also blocks absolute home-directory paths.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parent.parent
ALWAYS = [re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.I), re.compile(r"/(home|Users)/[a-z0-9_.-]+/", re.I)]


def staged_files() -> list[Path]:
  out = subprocess.run(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
    cwd=REPO, capture_output=True, text=True, check=True,
  ).stdout
  return [REPO / line for line in out.splitlines() if line.strip()]


def main() -> int:
  deny_file = REPO / ".private-strings"
  deny = []
  if deny_file.exists():
    deny = [s.strip() for s in deny_file.read_text(encoding="utf-8").splitlines() if s.strip() and not s.startswith("#")]
  patterns = ALWAYS + [re.compile(re.escape(s), re.I) for s in deny]

  files = sys.argv[1:] and [Path(a).resolve() for a in sys.argv[1:]] or staged_files()
  hits = []
  for f in files:
    if f.name == "check_private.py" or not f.is_file():
      continue
    try:
      text = f.read_text(encoding="utf-8")
    except UnicodeDecodeError:
      continue
    for n, line in enumerate(text.splitlines(), 1):
      for pat in patterns:
        if pat.search(line):
          hits.append(f"{f.relative_to(REPO)}:{n}: matches '{pat.pattern}'")
  if hits:
    print("Private strings found. Commit blocked:\n  " + "\n  ".join(hits))
    return 1
  return 0


if __name__ == "__main__":
  sys.exit(main())
