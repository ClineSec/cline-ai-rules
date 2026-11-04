"""Tracing and LangChain diagnostics, imported first by every dashboard process.

Spans go to the shared OpenTelemetry collector (deploy/docker-compose.yml). The analysts
asked to see the prompts behind odd answers, so the GenAI instrumentation records them.
"""

import logging
import os

from langchain_core.globals import set_debug
from langchain_core.tracers import ConsoleCallbackHandler

# Keep LangChain's step-by-step trace on while the prompt lab settles down.
LANGCHAIN_TRACE_STEPS = True

# Defaults only: anything set in the container environment wins.
TELEMETRY_ENV_DEFAULTS = {
    "OTEL_SEMCONV_STABILITY_OPT_IN": "gen_ai_latest_experimental",
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "span_and_event",
    "OTEL_SERVICE_NAME": "insights-dashboard",
}


def apply_telemetry_defaults(defaults: dict[str, str] = TELEMETRY_ENV_DEFAULTS) -> None:
    for key, value in defaults.items():
        os.environ.setdefault(key, value)


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def configure_langchain() -> None:
    set_debug(LANGCHAIN_TRACE_STEPS)


def lab_callbacks() -> list:
    """Callbacks for prompt-lab runs: the console tracer only on an analyst's laptop."""
    if os.environ.get("INSIGHTS_ENV") == "local":
        return [ConsoleCallbackHandler()]
    return []


apply_telemetry_defaults()
configure_logging(os.environ.get("INSIGHTS_LOG_LEVEL", "INFO"))
configure_langchain()
