import json, logging
from datetime import datetime, timezone
from app.core.request_id import get_request_id

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "traceId": get_request_id(),
        }

        for attr in ("path", "method", "status_code"):
            v = getattr(record, attr, None)
            if v is not None:
                data[attr] = v
        return json.dumps(data, ensure_ascii=False)

def configure_json_logging():
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # dämpa chattiga loggers 
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)