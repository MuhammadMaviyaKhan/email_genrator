class AppException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(AppException):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="VALIDATION_ERROR", status_code=422, details=details)


class NotFoundError(AppException):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="NOT_FOUND", status_code=404, details=details)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized", details: dict | None = None):
        super().__init__(message, code="UNAUTHORIZED", status_code=401, details=details)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden", details: dict | None = None):
        super().__init__(message, code="FORBIDDEN", status_code=403, details=details)


class ConflictError(AppException):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="CONFLICT", status_code=409, details=details)


class RateLimitError(AppException):
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", status_code=429, details={"retry_after": retry_after})


class EmailNotFoundError(NotFoundError):
    def __init__(self, email_id: str):
        super().__init__(f"Email with id {email_id} not found", details={"email_id": email_id})


class EmailAddressNotFoundError(NotFoundError):
    def __init__(self, address: str):
        super().__init__(f"Email address {address} not found", details={"address": address})


class EmailAddressExpiredError(ConflictError):
    def __init__(self, address: str):
        super().__init__(f"Email address {address} has expired", details={"address": address})


class EmailAddressBlockedError(ConflictError):
    def __init__(self, address: str):
        super().__init__(f"Email address {address} is blocked", details={"address": address})


class MaxEmailsReachedError(ConflictError):
    def __init__(self, address: str, max_emails: int):
        super().__init__(f"Maximum emails ({max_emails}) reached for {address}", details={"address": address, "max_emails": max_emails})


class InvalidEmailFormatError(ValidationError):
    def __init__(self, email: str):
        super().__init__(f"Invalid email format: {email}", details={"email": email})


class DomainNotAllowedError(ValidationError):
    def __init__(self, domain: str, allowed: list[str]):
        super().__init__(f"Domain {domain} is not allowed", details={"domain": domain, "allowed_domains": allowed})


class SessionExpiredError(UnauthorizedError):
    def __init__(self):
        super().__init__("Session has expired", details={"reason": "expired"})


class SessionInvalidError(UnauthorizedError):
    def __init__(self):
        super().__init__("Invalid session token", details={"reason": "invalid_token"})


class WebSocketError(AppException):
    def __init__(self, message: str, code: str = "WEBSOCKET_ERROR", details: dict | None = None):
        super().__init__(message, code=code, status_code=400, details=details)