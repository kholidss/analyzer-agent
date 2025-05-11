import logging
import structlog
import sys
import inspect
from typing import Any, List

class Field:
    def __init__(self, key: str, value: Any):
        self.key = key
        self.value = value

    def to_dict(self):
        return {self.key: self.value}

class Fields:
    def __init__(self):
        self.fields: List[Field] = []

    def append(self, key: str, value: Any):
        self.fields.append(Field(key, value))

    def to_dict(self):
        return {field.key: field.value for field in self.fields}
    

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

        log_method = getattr(self.logger, level.lower(), self.logger.info)

        log_method(message=message, event=self.fields.to_dict())

