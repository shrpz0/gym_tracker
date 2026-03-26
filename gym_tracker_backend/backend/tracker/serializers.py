from rest_framework import serializers
from .models import Set, Workout, Exercise, ExerciseSecondaryMuscle, ExerciseSecondaryLink
from django.db import transaction
from django.utils import timezone
from .models import LB_TO_KG, WeightUnit
from .utils import get_1RM_avg

class ExerciseSecondaryMuscleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSecondaryMuscle
        fields = ["id", "muscle_group"]

class ExerciseSerializer(serializers.ModelSerializer):
    secondary_muscles_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        write_only=True,
        required=False
    )
    secondary_muscles = ExerciseSecondaryMuscleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Exercise
        fields = [
            "id",
            "name", 
            "primary_muscle", 
            "secondary_muscles", 
            "pattern", 
            "region", 
            "is_compound",
            "secondary_muscles_ids"
        ]

    def validate_secondary_muscles_ids(self, ids):
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Duplicate secondary muscle ids are not allowed")
        
        existing = set(
            ExerciseSecondaryMuscle.objects.filter(id__in=ids).values_list("id", flat=True)
        )

        missing = [id for id in ids if id not in existing]
        if missing:
            raise serializers.ValidationError(f"Secondary muscles not found with id: {missing}")
        
        return ids

    @transaction.atomic
    def create(self, validated_data):
        secondary_ids = validated_data.pop("secondary_muscles_ids", [])
        exercise = Exercise.objects.create(**validated_data)

        if secondary_ids:
            links = [
                ExerciseSecondaryLink(exercise=exercise, secondary_id=sid) 
                    for sid in secondary_ids
            ]    
            ExerciseSecondaryLink.objects.bulk_create(links)

        return exercise

class WorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = [
            "id",
            "user", 
            "logged_at", 
            "note", 
            "rating"
        ]

        read_only_fields = ["user"]
    
    def validate_logged_at(self, value):
        if value is None:
            return timezone.now()
        return value
    
    def create(self, validated_data):
        user = self.context["request"].user
        return Workout.objects.create(user=user, **validated_data)
    
    
class SetSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(many=False, read_only=True)
    exercise_id = serializers.IntegerField(required=True, write_only=True)

    class Meta:
        model = Set
        fields = [
            "exercise_id",
            "exercise", 
            "reps",
            "weight",
            "unit",
            "estimated_1rm_kg",
            "weight_kg",
            "rir", 
            "workout",
        ]

        read_only_fields = [
            "estimated_1rm_kg"
        ]
    
        
        
    def validate_exercise_id(self, id):
        if id < 1:
            raise serializers.ValidationError("Incorrect Id")
        return id
    
    def create(self, validated_data):
        ex_id = validated_data.pop("exercise_id")

        if validated_data["unit"] == WeightUnit.LB:
            weight_kg = round(validated_data["weight"] * LB_TO_KG, 2)
        else:
            weight_kg = validated_data["weight"]

        if validated_data["reps"] > 1:
            rm = get_1RM_avg(weight_kg, validated_data["reps"])
        else:
            rm = weight_kg


        return Set.objects.create(exercise_id=ex_id, estimated_1rm_kg=rm, **validated_data)
        
