"""OpenTelemetry Distributed Tracing & Telemetry for Noetic.

Instruments LLM calls and pipeline executions with GenAI semantic conventions.
"""

from __future__ import annotations

from contextlib import contextmanager
import time
from typing import Generator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode

# Initialize TracerProvider if not already configured
if not isinstance(trace.get_tracer_provider(), TracerProvider):
  provider = TracerProvider()
  trace.set_tracer_provider(provider)

tracer = trace.get_tracer("noetic", "0.2.0")


@contextmanager
def trace_agent_call(
    agent_name: str,
    model: str | None = None,
    prompt_chars: int = 0,
) -> Generator[dict, None, None]:
  """Context manager to instrument an agent execution with OpenTelemetry."""
  start_time = time.time()
  metadata: dict = {
      "prompt_chars": prompt_chars,
      "completion_chars": 0,
      "cost_usd": None,
      "ok": True,
      "error": None,
  }

  with tracer.start_as_current_span(f"agent.{agent_name}") as span:
    span.set_attribute("gen_ai.system", agent_name)
    if model:
      span.set_attribute("gen_ai.request.model", model)
    span.set_attribute("gen_ai.usage.prompt_chars", prompt_chars)

    try:
      yield metadata
    except Exception as exc:
      metadata["ok"] = False
      metadata["error"] = str(exc)
      span.set_status(Status(StatusCode.ERROR, str(exc)))
      span.record_exception(exc)
      raise
    finally:
      latency_ms = (time.time() - start_time) * 1000.0
      span.set_attribute("gen_ai.latency_ms", latency_ms)
      if metadata.get("cost_usd") is not None:
        span.set_attribute("gen_ai.usage.cost_usd", metadata["cost_usd"])
      if metadata.get("completion_chars"):
        span.set_attribute(
            "gen_ai.usage.completion_chars", metadata["completion_chars"]
        )

      if metadata.get("ok"):
        span.set_status(Status(StatusCode.OK))
      elif metadata.get("error"):
        span.set_status(Status(StatusCode.ERROR, str(metadata["error"])))
