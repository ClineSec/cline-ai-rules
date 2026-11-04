FROM ghcr.io/example-org/litellm:1.106.3
COPY config.yaml /app/config.yaml
# ruleid: llm-debug-logging-enabled-env
ENV LITELLM_LOG DEBUG
# ruleid: llm-debug-logging-enabled-env
ENV PORT=4000 OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=span_and_event
# ok: llm-debug-logging-enabled-env
ENV OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT
EXPOSE 4000
# Append "--detailed_debug" to see raw requests while debugging.
# ruleid: llm-debug-logging-enabled-env
CMD ["--config", "/app/config.yaml", "--port", "4000", "--detailed_debug"]
