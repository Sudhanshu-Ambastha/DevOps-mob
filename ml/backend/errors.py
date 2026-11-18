from typing import Any


class AppError(Exception):
    def __init__(self, status:int, code:str, message:str, details:Any=None):
        super().__init__(message)
        self.status=status
        self.code=code
        self.message=message
        self.details=details


def not_found(what:str)->AppError:
    return AppError(404, "not_found", f"{what} was not found.")


def sign_in_required()->AppError:
    return AppError(401, "sign_in_required", "Please sign in to do this.")


def consent_required()->AppError:
    return AppError(403, "ai_consent_required", "Please accept the AI processing notice first.")
