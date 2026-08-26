import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.core.logging import request_id_var

logger = logging.getLogger("codesense.api")

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to inject Request IDs into contexts and response headers."""
    async def dispatch(self, request: Request, call_next) -> Response:
        # Check X-Request-ID header or generate a new UUID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
            
        token = request_id_var.set(request_id)
        
        start_time = time.perf_counter()
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time
            logger.info(
                f"Request completed: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {process_time:.4f}s"
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            process_time = time.perf_counter() - start_time
            logger.exception(
                f"Request failed: {request.method} {request.url.path} - "
                f"Error: {e!s} - Duration: {process_time:.4f}s"
            )
            raise e
        finally:
            request_id_var.reset(token)
