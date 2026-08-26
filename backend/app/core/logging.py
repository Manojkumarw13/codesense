import json
import logging
import sys
from contextvars import ContextVar
from typing import Any

from backend.app.core.settings import settings

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
job_id_var: ContextVar[str] = ContextVar("job_id", default="")
event_id_var: ContextVar[str] = ContextVar("event_id", default="")

class StructuredFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    def format(self, record: logging.LogRecord) -> str:
        # Prevent secret logging by filtering log message or attributes
        message = record.getMessage()
        
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "request_id": request_id_var.get(),
            "job_id": job_id_var.get(),
            "event_id": event_id_var.get(),
        }
        
        # Add extra fields if passed
        if hasattr(record, "extra") and isinstance(record.extra, dict): # type: ignore
            log_data.update(record.extra) # type: ignore
            
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)


class DevelopmentFormatter(logging.Formatter):
    """More readable formatter for local development."""
    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_var.get()
        req_str = f" [req_id={req_id}]" if req_id else ""
        
        msg = f"{self.formatTime(record, '%H:%M:%S')} | {record.levelname:<8} | {record.name} | {record.getMessage()}{req_str}"
        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)
        return msg


def setup_logging() -> None:
    """Setup logging configuration."""
    root_logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler(sys.stdout)
    
    if settings.APP_ENV == "production":
        formatter = StructuredFormatter()
    else:
        formatter = DevelopmentFormatter()
        
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    log_level = logging.INFO
    if settings.APP_ENV == "development":
        log_level = logging.DEBUG
        
    root_logger.setLevel(log_level)
    
    # Reduce noise from external libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
