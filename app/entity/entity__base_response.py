import json
from datetime import datetime
from typing import Any, List, Optional
from threading import Lock
from fastapi.responses import JSONResponse

class ErrorResp:
    def __init__(self, key: Optional[str] = None, messages: Optional[List[str]] = None):
        self.key = key
        self.messages = messages or []

    def to_dict(self):
        return {"key": self.key, "messages": self.messages}


class MetaData:
    def __init__(self, page: int = 0, limit: int = 0, total_page: int = 0, total_count: int = 0):
        self.page = page
        self.limit = limit
        self.total_page = total_page
        self.total_count = total_count

    def to_dict(self):
        return self.__dict__


class AppCtxResponse:
    _instance = None
    _lock = Lock()

    def __init__(self):
        self.code: Optional[int] = None
        self.status: bool = False
        self.timestamp: datetime = datetime.now()
        self.entity: Optional[str] = None
        self.state: Optional[str] = None
        self.message: Any = None
        self.meta: Any = None
        self.data: Any = None
        self.errors: List[ErrorResp] = []
        self.lang: Optional[str] = None
        self.msg_key: Optional[str] = None

    @classmethod
    def new(cls):
        with cls._lock:
            instance = cls()
            instance.timestamp = datetime.now()
            return instance

    def with_code(self, code: int):
        self.code = code
        self.status = code <= 201
        if code >= 500:
            self.message = "Internal server error"
        return self

    def with_entity(self, entity: str):
        self.entity = entity
        return self

    def with_state(self, state: str):
        self.state = state
        return self

    def with_data(self, data: Any):
        self.data = data
        return self

    def with_error(self, errors: List[ErrorResp]):
        self.errors = errors
        return self

    def with_msg_key(self, msg_key: str):
        self.msg_key = msg_key
        return self

    def with_meta(self, meta: Any):
        self.meta = meta
        return self

    def with_lang(self, lang: str):
        self.lang = lang
        return self

    def with_message(self, message: Any):
        self.message = message
        return self

    def to_dict(self, omit_empty: bool = False):
        raw = {
            "code": self.code,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "entity": self.entity,
            "state": self.state,
            "message": self.message,
            "meta": self.meta.to_dict() if hasattr(self.meta, "to_dict") else self.meta,
            "data": self.data,
            "errors": [e.to_dict() for e in self.errors] if self.errors else None
        }

        if not omit_empty:
            return raw
        
        return {k: v for k, v in raw.items() if v not in (None, [], {}, "")}

    def to_json(self):
        return json.dumps(self.to_dict(), default=str)
    
    def json(self):
        return JSONResponse(status_code=self.code, content=self.to_dict(omit_empty=True))
