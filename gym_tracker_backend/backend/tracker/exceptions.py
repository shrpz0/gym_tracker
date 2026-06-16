from rest_framework.exceptions import APIException

class StrengthEvaluationUpdateError(APIException):
    status_code = 500
    default_detail = "Failed to Update Strength Evaluation From New PR"
    default_code = "strength_evaluation_update_failed"

class DomainError(Exception):
    default_code = "domain_error"

    def __init__(self, message=None, code=None, extra=None):
        self.message = message or "Domain Error."
        self.code = code or self.default_code
        self.extra = extra or {}

class InvalidPRCreationError(DomainError):
    default_code = "invalid_pr_creation"

