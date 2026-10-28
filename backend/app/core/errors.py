from typing import Any


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, details: dict[str, Any] | None = None):
        self.code, self.message, self.status = code, message, status
        self.details = details or {}
        super().__init__(message)


def not_implemented(feature: str) -> None:
    raise AppError("NOT_IMPLEMENTED", "This feature is assigned for implementation after the foundation handoff.", 501, {"feature": feature})
