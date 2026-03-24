from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Workout, Set, Exercise, ExerciseSecondaryMuscle
from .serializers import WorkoutSerializer, SetSerializer, ExerciseSecondaryMuscleSerializer, ExerciseSerializer

class SetViewSet(ModelViewSet):
    queryset = Set.objects.all()
    serializer_class = SetSerializer

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
        if scope == "day":
            return Response({"G":"DL"})
        return Response({"Loser":"DL"})
        