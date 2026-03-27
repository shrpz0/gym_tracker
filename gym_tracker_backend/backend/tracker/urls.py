from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExerciseViewSet, ExerciseSecondaryMuscleViewSet, WorkoutViewSet, SetViewSet, AggregateWorkoutsAPIView, PRViewSet

router = DefaultRouter()
router.register(r"Workout", WorkoutViewSet)
router.register(r"Exercise", ExerciseViewSet)
router.register(r"Set", SetViewSet)
router.register(r"ExerciseSecondaryMuscle", ExerciseSecondaryMuscleViewSet)
router.register(r"PR", PRViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("analytics/aggregate_workouts/<str:scope>/", AggregateWorkoutsAPIView.as_view())
]