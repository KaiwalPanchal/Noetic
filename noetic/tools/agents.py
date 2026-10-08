"""Compatibility forwarder: agents module moved to noetic.agents.runners."""

from noetic.agents.runners import *  # noqa: F401, F403
import noetic.agents.runners as _runners

# Ensure module attributes are accessible
for attr in dir(_runners):
    if not attr.startswith("__"):
        globals()[attr] = getattr(_runners, attr)
