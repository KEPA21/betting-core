import logging
from opentelemetry import trace


class TraceContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        sc = trace.get_current_span().get_span_context()
        record.trace_id = format(sc.trace_id, "032x") if sc and sc.is_valid else None
        record.span_id = format(sc.span_id, "016x") if sc and sc.is_valid else None
        return True
