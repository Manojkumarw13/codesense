import json
import logging

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from backend.app.core.exceptions import (
    NotFoundError,
    register_exception_handlers,
)
from backend.app.core.logging import (
    DevelopmentFormatter,
    StructuredFormatter,
    request_id_var,
)
from backend.app.core.settings import settings


def test_settings_uri():
    """Verify Settings class SQLALCHEMY_DATABASE_URI construction."""
    assert settings.APP_NAME == "CodeSense"
    assert "postgresql://" in settings.SQLALCHEMY_DATABASE_URI


def test_exception_response_format():
    """Verify that exception handlers format error responses correctly with request ID."""
    app = FastAPI()
    register_exception_handlers(app)
    
    @app.get("/trigger-codesense-error")
    def trigger_cs():
        raise NotFoundError("Project XYZ not found")
        
    @app.get("/trigger-generic-error")
    def trigger_gen():
        raise ValueError("Something bad happened")

    client = TestClient(app, raise_server_exceptions=False)
    
    # 1. Test CodeSense Custom Error (404)
    request_id_var.set("test-request-id-1")
    response = client.get("/trigger-codesense-error")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert data["error"]["message"] == "Project XYZ not found"
    assert data["request_id"] == "test-request-id-1"

    # 2. Test Generic Exception (500)
    request_id_var.set("test-request-id-2")
    response = client.get("/trigger-generic-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert data["request_id"] == "test-request-id-2"


def test_logging_formatters():
    """Verify custom logging formatters serialize/format properly."""
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test log message",
        args=(),
        exc_info=None
    )
    
    # Setup context vars
    token = request_id_var.set("test-log-req")
    
    try:
        # Test StructuredFormatter (JSON output)
        sf = StructuredFormatter()
        formatted_json = sf.format(record)
        data = json.loads(formatted_json)
        assert data["message"] == "Test log message"
        assert data["request_id"] == "test-log-req"
        assert data["level"] == "INFO"
        
        # Test DevelopmentFormatter
        df = DevelopmentFormatter()
        formatted_dev = df.format(record)
        assert "INFO" in formatted_dev
        assert "Test log message" in formatted_dev
        assert "test-log-req" in formatted_dev
    finally:
        request_id_var.reset(token)
