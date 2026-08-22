from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from backend.app.core.logging import request_id_var

class CodeSenseException(Exception):
    """Base exception for all CodeSense application errors."""
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(CodeSenseException):
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ValidationError(CodeSenseException):
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            code="VALIDATION_FAILED",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class AuthenticationError(CodeSenseException):
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            code="AUTHENTICATION_FAILED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(CodeSenseException):
    def __init__(self, message: str = "Not authorized", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            code="AUTHORIZATION_FAILED",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ConflictError(CodeSenseException):
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class DatabaseError(CodeSenseException):
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            code="DATABASE_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class AIError(CodeSenseException):
    def __init__(self, message: str = "AI gateway error", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            code="AI_ERROR",
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for the FastAPI app."""
    
    @app.exception_handler(CodeSenseException)
    async def codesense_exception_handler(request: Request, exc: CodeSenseException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                },
                "request_id": request_id_var.get()
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Format Pydantic errors into details dict
        from fastapi.encoders import jsonable_encoder
        details = {"errors": jsonable_encoder(exc.errors())}
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_FAILED",
                    "message": "Input validation failed",
                    "details": details
                },
                "request_id": request_id_var.get()
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "details": {}
                },
                "request_id": request_id_var.get()
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Wrap unknown errors as standard 500
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred on the server",
                    "details": {"error_class": exc.__class__.__name__, "error_detail": str(exc)}
                },
                "request_id": request_id_var.get()
            }
        )
