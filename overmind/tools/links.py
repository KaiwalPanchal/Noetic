"""Tools layer: deterministic link check.

Agents sometimes invent plausible URLs. This verifies a URL actually resolves.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request


def url_ok(url: str, timeout: int = 12) -> bool:
  """True if the URL exists. Bot-blocking (401/403/429) counts as alive."""
  yt = re.search(r"youtube\.com/watch\?v=([^&]+)|youtu\.be/([^?&/]+)", url)
  if yt and not re.fullmatch(r"[A-Za-z0-9_-]{11}", yt.group(1) or yt.group(2)):
    return False  # YouTube serves 200 for any id; real ids are 11 chars
  req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (taste-engine link check)"})
  try:
    with urllib.request.urlopen(req, timeout=timeout) as resp:
      return resp.status < 400
  except urllib.error.HTTPError as exc:
    return exc.code in (401, 403, 405, 429, 999)
  except Exception:
    return False
