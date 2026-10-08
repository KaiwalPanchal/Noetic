"""Tests for Twitter/X thread length weighting and validation."""

from pathlib import Path
from noetic.tools.tweets import weighted_length, too_long
from workflows.twitter.scripts.thread_validator import parse_thread, validate_thread


def test_weighted_length_plain_ascii():
  text = "Hello world! This is a simple test."
  assert weighted_length(text) == len(text)


def test_weighted_length_url_is_23_chars():
  # Regardless of URL length, X counts it as 23 chars
  short_url = "https://a.co"
  long_url = "https://example.com/very/long/path/with/query?parameters=1234567890"

  assert weighted_length(short_url) == 23
  assert weighted_length(long_url) == 23
  assert weighted_length(f"Check {long_url} out") == 6 + 23 + 4  # "Check " (6) + 23 + " out" (4)


def test_weighted_length_emoji_and_cjk():
  # Emoji counts as 2 chars
  emoji_text = "🚀"
  assert weighted_length(emoji_text) == 2

  cjk_text = "日本語"
  assert weighted_length(cjk_text) == 6


def test_too_long_detector():
  tweets = ["Short tweet", "A" * 300]
  warnings = too_long(tweets, 280)
  assert len(warnings) == 1
  assert "tweet 2 is 300 chars" in warnings[0]


def test_parse_thread(tmp_path: Path):
  thread_file = tmp_path / "thread.md"
  thread_file.write_text(
      """# Thread Title

### Tweet 1 (Hook)
First tweet text here.

---

### Tweet 2
Second tweet text here.
""",
      encoding="utf-8",
  )

  parsed = parse_thread(thread_file)
  assert len(parsed) == 2
  assert "Tweet 1" in parsed[0][0]
  assert parsed[0][1] == "First tweet text here."
  assert "Tweet 2" in parsed[1][0]
  assert parsed[1][1] == "Second tweet text here."


def test_validate_thread_passes(tmp_path: Path):
  thread_file = tmp_path / "valid_thread.md"
  thread_file.write_text(
      """### Tweet 1
This is well within the 280 character limit.
""",
      encoding="utf-8",
  )

  assert validate_thread(thread_file, 280) is True


def test_validate_thread_fails_on_length(tmp_path: Path):
  thread_file = tmp_path / "invalid_thread.md"
  thread_file.write_text(
      f"""### Tweet 1
{'A' * 300}
""",
      encoding="utf-8",
  )

  assert validate_thread(thread_file, 280) is False
