from typing import Optional, Dict, Any


class AppException(Exception):
    """Base application exception"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """Validation error"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class AuthenticationException(AppException):
    """Authentication error"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message, status_code=401, error_code="AUTHENTICATION_REQUIRED"
        )


class AuthorizationException(AppException):
    """Authorization error"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, status_code=403, error_code="FORBIDDEN")


class NotFoundException(AppException):
    """Resource not found"""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
        )


class ConflictException(AppException):
    """Resource conflict"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message, status_code=409, error_code="CONFLICT", details=details
        )


class RateLimitException(AppException):
    """Rate limit exceeded"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message, status_code=429, error_code="RATE_LIMIT_EXCEEDED"
        )


class BudgetExceededException(AppException):
    """Budget limit exceeded"""

    def __init__(self, remaining_budget: float):
        super().__init__(
            message="Daily budget exceeded",
            status_code=429,
            error_code="BUDGET_EXCEEDED",
            details={"remaining_budget_usd": remaining_budget},
        )
