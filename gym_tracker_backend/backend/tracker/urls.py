from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (ExerciseViewSet, ExerciseSecondaryMuscleViewSet,
                    WorkoutViewSet, SetViewSet, AggregateWorkoutsAPIView, 
                    PRViewSet, ProfileViewSet, StrengthStandardViewSet,
                    MuscleStrengthIndicatorViewSet, ExerciseStrengthEvaluationViewSet, StrengthProfileAPIView)

router = DefaultRouter()
router.register(r"Workout", WorkoutViewSet)
router.register(r"Exercise", ExerciseViewSet)
router.register(r"Set", SetViewSet)
router.register(r"ExerciseSecondaryMuscle", ExerciseSecondaryMuscleViewSet)
router.register(r"PR", PRViewSet)
router.register(r"Profile", ProfileViewSet)
router.register(r"StrengthStandard", StrengthStandardViewSet)
router.register(r"MuscleStrengthIndicator", MuscleStrengthIndicatorViewSet)
router.register(r"ExerciseStrengthEvaluation", ExerciseStrengthEvaluationViewSet)




urlpatterns = [
    path("", include(router.urls)),
    path("analytics/aggregate_workouts/<str:scope>/", AggregateWorkoutsAPIView.as_view()),
    path("strengthprofile/", StrengthProfileAPIView.as_view())
]