import logging
import sys
from pythonjsonlogger import jsonlogger


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for field in ["trace_id", "span_id", "wallet_id", "transaction_id", "idempotency_key"]:
            if not hasattr(record, field):
                setattr(record, field, None)
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(trace_id)s %(span_id)s %(wallet_id)s %(transaction_id)s %(idempotency_key)s"
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    root.addFilter(ContextFilter())
