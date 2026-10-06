"""Twitter/X Thread Validator and Linter.

Checks per-tweet length for markdown thread drafts using `### Tweet N` headers.
Length follows X's weighting: every URL counts as 23 characters, and emoji /
CJK characters count as 2. Exits with code 1 when any tweet is over the limit,
so agents and hooks can gate on it.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from taste_engine.tools.tweets import weighted_length  # noqa: E402,F401

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
  sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
  sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_LIMIT = 280


def parse_thread(file_path: Path) -> list[tuple[str, str]]:
  content = file_path.read_text(encoding="utf-8")
  # Look for headers like '### Tweet 1 (Hook)' or '### Tweet 1'
  chunks = re.split(r"(?=###\s+Tweet\s+\d+)", content)
  tweets = []

  for chunk in chunks:
    chunk = chunk.strip()
    if not chunk or not chunk.startswith("###"):
      continue

    lines = chunk.splitlines()
    header = lines[0].strip()
    body = "\n".join(lines[1:]).strip()
    # Strip any trailing hr, and anything after it (notes between tweets)
    body = re.split(r"\n---\s*(\n|$)", body)[0].strip()
    tweets.append((header, body))

  return tweets


def validate_thread(file_path: Path, limit: int) -> bool:
  if not file_path.exists():
    print(f"Error: File not found: {file_path}", file=sys.stderr)
    sys.exit(2)

  tweets = parse_thread(file_path)
  if not tweets:
    print("Warning: No '### Tweet N' sections found in file.")
    return False

  print("=" * 65)
  print(f"VALIDATING THREAD: {file_path.name}")
  print("=" * 65)

  all_passed = True
  for header, body in tweets:
    count = weighted_length(body)
    ok = count <= limit and bool(body)
    all_passed &= ok
    status = "PASS" if ok else ("FAIL (EMPTY)" if not body else "FAIL (TOO LONG)")
    print(f"\n{header} [{status}]")
    print(f"Length: {count}/{limit} (X-weighted)")
    print("-" * 40)
    print(body)
    print("-" * 40)

  print("\n" + "=" * 65)
  if all_passed:
    print(f"SUCCESS: All {len(tweets)} tweets are within the {limit}-character limit.")
  else:
    print("FAIL: Fix the flagged tweets before shipping.")
  print("=" * 65)
  return all_passed


def main():
  parser = argparse.ArgumentParser(description="Validate Twitter/X thread drafts")
  parser.add_argument("file", type=str, help="Path to thread markdown file")
  parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Per-tweet limit (default 280)")
  args = parser.parse_args()

  sys.exit(0 if validate_thread(Path(args.file), args.limit) else 1)


if __name__ == "__main__":
  main()
