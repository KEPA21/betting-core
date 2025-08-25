import logging
import json
import sys
from contextvars import ContextVar
from app.observability.trace_filter import TraceContextFilter

request_id_var = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", request_id_var.get()),
            "method": getattr(record, "method", None),
            "path": getattr(record, "path", None),
            "status": getattr(record, "status", None),
            "latency_ms": getattr(record, "latency_ms", None),
        }
        if record.exc_info:
            payload["exc_type"] = record.ext_info[0].__name__
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO"):
    root = logging.getLogger()
    root.addFilter(TraceContextFilter())
    root.handlers[:] = []
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(JsonFormatter())
    root.addHandler(h)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    logging.getLogger("uvicorn.access").addFilter(TraceContextFilter())
