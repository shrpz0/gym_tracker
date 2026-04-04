from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
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
from .services.prs import update_pr_new_set
from rest_framework import status
from .services.prs import handle_pr_set_deletion

class SetViewSet(ModelViewSet):
    queryset = Set.objects.all()
    serializer_class = SetSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_instance = serializer.save()

        pr_result = update_pr_new_set(set_instance)
        response_serializer = self.get_serializer(set_instance)
        success_headers = self.get_success_headers(response_serializer.data)

        return Response(
            {
                "set" : response_serializer.data,
                "pr_event" : pr_result
            },
            status=status.HTTP_201_CREATED,
            headers=success_headers
        )
    
    def destroy(self, request, *args, **kwargs):
        set_instance = self.get_object()

        try:
            pr = set_instance.pr
        except PR.DoesNotExist:
            pr = None

        if pr and set_instance.reps < 9:
            pr_exercise_id=set_instance.exercise_id
            pr_type=set_instance.pr.pr_type
            pr_user_id=set_instance.workout.user_id
        else:
            return super().destroy(request, *args, **kwargs)
    

        super().destroy(request, *args, **kwargs)
        new_pr = handle_pr_set_deletion(
            pr_exercise_id=pr_exercise_id,
            pr_type=pr_type,
            pr_user_id=pr_user_id
        )

        if new_pr:
            new_pr_data = PRSerializer(instance=new_pr).data
            return Response(
                {
                    "new_pr": new_pr_data,
                },
                status=status.HTTP_202_ACCEPTED
            )

        return Response({}, status=status.HTTP_204_NO_CONTENT)

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
        

class PRViewSet(ModelViewSet):
    queryset = PR.objects.all()
    serializer_class = PRSerializer

class StrengthStandardViewSet(ModelViewSet):
    queryset = StrengthStandard.objects.all()
    serializer_class = StrengthStandardSerializer

class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

class MuscleStrengthIndicatorViewSet(ModelViewSet):
    queryset = MuscleStrengthIndicator.objects.all()
    serializer_class = MuscleStrengthIndicatorSerializer


class ExerciseStrengthEvaluationViewSet(ModelViewSet):
    queryset = ExerciseStrengthEvaluation.objects.all()
    serializer_class = ExerciseStrengthEvaluationSerializer