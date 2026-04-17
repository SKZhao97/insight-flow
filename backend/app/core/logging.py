import logging
from contextvars import ContextVar


request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="-")


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        record.trace_id = trace_id_ctx.get()
        return True


def configure_logging(level: str = "INFO") -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s trace_id=%(trace_id)s] %(message)s"
            )
        )
        handler.addFilter(RequestContextFilter())
        root_logger.addHandler(handler)
        return

    for handler in root_logger.handlers:
        handler.addFilter(RequestContextFilter())


def bind_request_context(request_id: str, trace_id: str) -> None:
    request_id_ctx.set(request_id)
    trace_id_ctx.set(trace_id)


def clear_request_context() -> None:
    request_id_ctx.set("-")
    trace_id_ctx.set("-")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
