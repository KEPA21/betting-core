# app/observability/tracing.py
import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
except Exception:
    OTLPSpanExporter = None

from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor


def setup_tracing(app, engine):
    if os.getenv("ENABLE_TRACING", "false").lower() not in ("1", "true", "yes"):
        return

    service_name = os.getenv("OTEL_SERVICE_NAME", "betting-core")
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    trace.set_tracer_provider(provider)

    # Välj exporter: OTLP om endpoint finns, annars Console
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint and OTLPSpanExporter:
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=otlp_endpoint,
                    headers=os.getenv("OTEL_EXPORTER_OTLP_HEADERS"),
                )
            )
        )
    else:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    # Preferera FastAPI-instrumentering (namnger routes), fallback till ASGI-middleware
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor().instrument_app(app)
    except Exception:
        try:
            from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware

            app.add_middleware(OpenTelemetryMiddleware)
        except Exception:
            pass

    # SQLAlchemy spans
    try:
        SQLAlchemyInstrumentor().instrument(engine=engine)
    except Exception as e:
        print(f"SQLAlchemy instrumentation failed: {e}")
