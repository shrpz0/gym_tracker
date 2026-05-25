from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import IsOwner
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
from .utils import get_week_range, get_month_range
from .services.analytics import get_review
from .services.prs import handle_new_set, handle_set_deleted
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
        return Workout.objects.filter(user=user)
    

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
                ), status=status.HTTP_200_OK
            )
        
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
