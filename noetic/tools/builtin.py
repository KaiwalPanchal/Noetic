"""Tools layer: built-in core tools.

Registers the standard set of deterministic utility tools available to agents.
Imports dependencies lazily to keep registry discovery fast.
"""

from __future__ import annotations

from typing import Any

from noetic.tools.registry import tool


@tool("clip_url", help="statelessly fetch and clip a webpage into structured markdown")
def clip_url(url: str, timeout: int = 15) -> dict[str, Any]:
  from noetic.tools import clipper
  return clipper.clip_url(url, timeout=timeout)


@tool("verify_url", help="verify that a URL resolves alive")
def verify_url(url: str) -> bool:
  from noetic.tools import links
  return links.url_ok(url)


@tool("check_schema", help="validate data against a registered schema by name")
def check_schema(data: Any, schema_name: str) -> list[str]:
  from noetic.tools import prompts, schema_check
  return schema_check.check(data, prompts.schema(schema_name))


@tool("tweet_length", help="calculate weighted character length of text as counted by X")
def tweet_length(text: str) -> int:
  from noetic.tools import tweets
  return tweets.weighted_length(text)
