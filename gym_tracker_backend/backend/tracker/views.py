from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Workout, Set, Exercise, ExerciseSecondaryMuscle
from .serializers import WorkoutSerializer, SetSerializer, ExerciseSecondaryMuscleSerializer, ExerciseSerializer
from django.utils import timezone
from .utils import get_week_range, get_month_range
from .services.analytics import get_review
from .services.prs import update_pr_for_set

class SetViewSet(ModelViewSet):
    queryset = Set.objects.all()
    serializer_class = SetSerializer

    def perform_create(self, serializer):
        set_instance = serializer.save()
        update_pr_for_set(set_instance)

class ExerciseViewSet(ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer

class ExerciseSecondaryMuscleViewSet(ModelViewSet):
    queryset = ExerciseSecondaryMuscle.objects.all()
    serializer_class = ExerciseSecondaryMuscleSerializer

class WorkoutViewSet(ModelViewSet):
    queryset = Workout.objects.all()
    serializer_class = WorkoutSerializer

class AggregateWorkoutsAPIView(APIView):
    def get(self, request, scope):
        user = request.user

        if scope == "week":
            today = timezone.localdate()
            start_dt, end_dt = get_week_range(today)
            return Response(
                data=get_review(
                    start_date=start_dt, end_date=end_dt, user=user
                    )
                )

        elif scope == "month":
            today = timezone.localdate()
            start_dt, end_dt = get_month_range(today)
            return Response(
                data=get_review(
                    start_date=start_dt, end_date=end_dt, user=user
                )
            )
        

        
