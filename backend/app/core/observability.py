"""Observability layer – Phase 2 Infrastructure Foundation.

Provides:
- Prometheus metrics (prometheus_client) with graceful fallback if not installed
- OpenTelemetry tracing setup (optional, no-op if unavailable)
- Helpers for API / ingestion / worker observability
"""
import logging
import time
from typing import Optional

from fastapi import Request, Response

logger = logging.getLogger("codesense.observability")

# Prometheus metrics – try to import, else stub
try:
    from prometheus_client import Counter, Histogram, Gauge, REGISTRY, generate_latest, CONTENT_TYPE_LATEST  # type: ignore

    REQUEST_COUNT = Counter(
        "codesense_http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
    )
    REQUEST_LATENCY = Histogram(
        "codesense_http_request_duration_seconds",
        "HTTP request latency",
        ["method", "path"],
    )
    INGESTION_COUNTER = Counter(
        "codesense_ingestion_events_total",
        "Ingestion events by status",
        ["status"],
    )
    DB_QUERY_DURATION = Histogram(
        "codesense_db_query_duration_seconds",
        "DB query duration",
    )
    WORKER_JOBS_PROCESSED = Counter(
        "codesense_worker_jobs_processed_total",
        "Worker jobs processed",
    )
    WORKER_DURATION = Histogram(
        "codesense_worker_duration_seconds",
        "Worker job duration",
    )
    WORKER_HEARTBEAT = Counter(
        "codesense_worker_heartbeat_total",
        "Worker heartbeats",
    )
    CACHE_HITS = Counter("codesense_cache_hits_total", "Cache hits", ["result"])
    METRICS_ENABLED = True

    def metrics_response():  # type: ignore[no-untyped-def]
        data = generate_latest(REGISTRY)
        from fastapi.responses import Response as FastapiResponse

        return FastapiResponse(content=data, media_type=CONTENT_TYPE_LATEST)

except Exception as exc:  # noqa: BLE001
    logger.warning(f"prometheus_client not available ({exc}); metrics disabled")
    REQUEST_COUNT = None  # type: ignore
    REQUEST_LATENCY = None  # type: ignore
    INGESTION_COUNTER = None  # type: ignore
    DB_QUERY_DURATION = None  # type: ignore
    WORKER_JOBS_PROCESSED = None  # type: ignore
    WORKER_DURATION = None  # type: ignore
    WORKER_HEARTBEAT = None  # type: ignore
    CACHE_HITS = None  # type: ignore
    METRICS_ENABLED = False

    def metrics_response():  # type: ignore[no-untyped-def]
        from fastapi.responses import JSONResponse

        return JSONResponse({"status": "metrics_disabled", "reason": str(exc)})


# OpenTelemetry – optional no-op
_tracer = None


def setup_tracing(service_name: str = "codesense-api"):
    """Setup OpenTelemetry tracing if available."""
    global _tracer
    try:
        from opentelemetry import trace  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter  # type: ignore

        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(service_name)
        logger.info("OpenTelemetry tracing enabled")
        # OTLP exporter if configured
        from backend.app.core.settings import settings

        if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # type: ignore
                from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore

                otlp_exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                logger.info(f"OTLP exporter -> {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"OTLP exporter failed: {e}")
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Tracing disabled ({exc})")
        _tracer = None


def get_tracer():  # type: ignore[no-untyped-def]
    return _tracer


# Middleware helper
class PrometheusMiddleware:
    """ASGI middleware to record http metrics – lightweight."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not METRICS_ENABLED:
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")

        # Normalize path for cardinality (keep prefix)
        # e.g., /api/v1/events -> /api/v1/events, but dynamic ids -> template
        # Simple heuristic: keep first 4 segments
        # We expose raw path for now; Prometheus handles cardinality via label
        start = time.perf_counter()

        status_code = "200"

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = str(message.get("status", 200))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.perf_counter() - start
            try:
                if REQUEST_COUNT:
                    REQUEST_COUNT.labels(method=method, path=path, status=status_code).inc()
                if REQUEST_LATENCY:
                    REQUEST_LATENCY.labels(method=method, path=path).observe(duration)
            except Exception:
                pass
