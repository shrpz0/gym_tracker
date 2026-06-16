from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from .permissions import IsOwner
from .utils import start_of_day, start_of_next_day
from .services.analytics import get_stats
from .models import (Workout, Set, Exercise, ExerciseSecondaryMuscle,
                    PR, StrengthStandard, Profile,
                    MuscleStrengthIndicator, ExerciseStrengthEvaluation)
from .serializers import (WorkoutSerializer, SetSerializer,
                         ExerciseSecondaryMuscleSerializer, 
                         ExerciseSerializer, PRSerializer, 
                         StrengthStandardSerializer, ProfileSerializer,
                         MuscleStrengthIndicatorSerializer,
                         ExerciseStrengthEvaluationSerializer
                    )

from django.utils import timezone
from django.db.models import Prefetch
from .utils import get_week_range, get_month_range
from .services.prs import handle_new_set, handle_set_deleted, handle_workout_deleted
from rest_framework import status
from .services.strength_evaluations import update_exercise_strength_evaluation
from .services.strengthprofile import get_strength_profile
from rest_framework.permissions import IsAuthenticated


class SetViewSet(ModelViewSet):
    queryset = Set.objects.all()
    serializer_class = SetSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        user = self.request.user
        return Set.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_instance = serializer.save()

        events = handle_new_set(set_instance=set_instance)
        
        response_serializer = self.get_serializer(set_instance)
        success_headers = self.get_success_headers(response_serializer.data)

        return Response(
            {
                "set" : response_serializer.data,
                "events": events
            },
            status=status.HTTP_201_CREATED,
            headers=success_headers
        )
    

    def destroy(self, request, *args, **kwargs):
        set_instance = self.get_object()
        result = handle_set_deleted(set_instance)

        if result is None:
            return Response({"events": result}, status=204)

        return Response(result, status=200)


class ExerciseViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer

class ExerciseSecondaryMuscleViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = ExerciseSecondaryMuscle.objects.all()
    serializer_class = ExerciseSecondaryMuscleSerializer

class WorkoutViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Workout.objects.all()
    serializer_class = WorkoutSerializer

    def get_queryset(self):
        user = self.request.user
        
        qs = (
            Workout
            .objects
            .filter(user=user)
            .prefetch_related(
                Prefetch(
                    "sets",
                    queryset=(
                        Set
                        .objects
                        .select_related("exercise")
                        .prefetch_related("exercise__secondary_muscles"))
                )
            )
        )

        return qs
    
    def destroy(self, request, *args, **kwargs):
        workout_instance = self.get_object()

        data = handle_workout_deleted(workout_instance)

        return Response({
            "ACTION": "Workout DELETED",
            "DETAIL": data
        }, status=status.HTTP_200_OK)

        
    

class GetWorkoutStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not start_date or not end_date:
            return ValidationError("start_date and end_date are required.")
        
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        if not start_date or not end_date:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD.")
        
        if start_date >= end_date:
            raise ValidationError("start_date must be before end_date.")
        
        start_dt = start_of_day(start_date)
        end_dt = start_of_next_day(end_date)

        data = get_stats(start_dt=start_dt, end_dt=end_dt, user=user)
        return Response(data)


        
class StrengthProfileAPIView(APIView):
    def get(self, request):
        user_id = request.user.id
        results = get_strength_profile(user_id=user_id)
        return Response(
            data=results, status=status.HTTP_200_OK
        )     

class PRViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    http_method_names = ["get"]

    queryset = PR.objects.all()
    serializer_class = PRSerializer

    def get_queryset(self):
        user = self.request.user
        return PR.objects.filter(user=user)

    

class StrengthStandardViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    queryset = StrengthStandard.objects.all()
    serializer_class = StrengthStandardSerializer


class ProfileViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]

    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def get_queryset(self):
        user = self.request.user
        return Profile.objects.filter(user=user)

class MuscleStrengthIndicatorViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    queryset = MuscleStrengthIndicator.objects.all()
    serializer_class = MuscleStrengthIndicatorSerializer


class ExerciseStrengthEvaluationViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    http_method_names = ["get"]

    queryset = ExerciseStrengthEvaluation.objects.all()
    serializer_class = ExerciseStrengthEvaluationSerializer

    def get_queryset(self):
        user = self.request.user
        return ExerciseStrengthEvaluation.objects.filter(user=user)
