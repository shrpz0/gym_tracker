from rest_framework.exceptions import APIException

class StrengthEvaluationUpdateError(APIException):
    status_code = 500
    default_detail = "Failed to Update Strength Evaluation From New PR"
    default_code = "strength_evaluation_update_failed"


