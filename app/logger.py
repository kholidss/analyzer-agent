import logging
import structlog
import sys
import inspect
from typing import Any, List, Dict
from app.util.context import request_id_ctx


class Field:
    def __init__(self, key: str, value: Any):
        self.key = key
        self.value = value


class Fields:
    def __init__(self):
        self.fields: List[Field] = []

    def append(self, key: str, value: Any):
        self.fields.append(Field(key, value))

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for field in self.fields:
            self._merge_dict(result, field.key, field.value)
        return result

    def _merge_dict(self, base: Dict[str, Any], dotted_key: str, value: Any):
        parts = dotted_key.split(".")
        current = base
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value


def add_caller_info(logger, method_name, event_dict):
    for frame_info in inspect.stack():
        filepath = frame_info.filename
        if all(x not in filepath for x in ("structlog", "logging", "logger.py")):
            event_dict["file"] = filepath
            event_dict["line"] = frame_info.lineno
            event_dict["function"] = frame_info.function
            break

    event_dict["level"] = event_dict.get("level", method_name.upper())
    event_dict["message"] = event_dict.get("message", "No message provided")

    return event_dict


class AppCtxLogger:
    def __init__(self):
        self._configure_structlog()
        self.logger = structlog.get_logger()
        self.fields = Fields()

    def _configure_structlog(self):
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=logging.INFO,
        )

        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                add_caller_info,
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    def event_name(self, name: str):
        self.fields.append("name", name)

    def field(self, key: str, value: Any):
        self.fields.append(key, value)

    def info(self, message, **kwargs):
        self._stdout("info", message, **kwargs)

    def warning(self, message, **kwargs):
        self._stdout("warning", message, **kwargs)

    def error(self, message, **kwargs):
        self._stdout("error", message, **kwargs)

    def debug(self, message, **kwargs):
        self._stdout("debug", message, **kwargs)

    def _stdout(self, level, message, **kwargs):
        for key, value in kwargs.items():
            self.fields.append(key, value)

        log_data = {
            "prerequest": {
                "request_id": request_id_ctx.get()
            },
            "event": self.fields.to_dict()
        }

        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message=message, **log_data)
