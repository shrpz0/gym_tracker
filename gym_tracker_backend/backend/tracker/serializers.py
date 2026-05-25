from rest_framework import serializers
from .models import (Set, Workout, Exercise, ExerciseSecondaryMuscle, 
                     ExerciseSecondaryLink, PR, StrengthStandard, 
                     Profile, MuscleStrengthIndicator, ExerciseStrengthEvaluation
                    )
from django.db import transaction
from django.utils import timezone
from .models import LB_TO_KG, WeightUnit
from .utils import get_1RM_avg, get_weeks_passed

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
        
        weeks_passed = get_weeks_passed(dt=value)
        if weeks_passed >= 48:
            raise serializers.ValidationError(
                "You can only log workouts from the last 48 weeks."
            )
        
        if value > timezone.now():
            raise serializers.ValidationError(
                "Workout date cannot be in the future."
            )
        
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
            "id",
            "exercise_id",
            "exercise", 
            "logged_at",
            "user",
            "reps",
            "weight",
            "unit",
            "e1rm_kg",
            "weight_kg",
            "rir", 
            "workout",
        ]

        read_only_fields = [
            "e1rm_kg",
            "logged_at"
        ]
    
        
        
    def validate_exercise_id(self, id):
        if id < 1:
            raise serializers.ValidationError("Incorrect Id")
        return id
    
    def create(self, validated_data):
        ex_id = validated_data.pop("exercise_id")

        validated_data.pop("user")
        user = self.context["request"].user

    

        if validated_data["unit"] == WeightUnit.LB:
            weight_kg = round(validated_data["weight"] * LB_TO_KG, 2)
        else:
            weight_kg = validated_data["weight"]

        if validated_data["reps"] > 1:
            rm = get_1RM_avg(weight_kg, validated_data["reps"])
        else:
            rm = weight_kg

        logged_at = validated_data["workout"].logged_at

        return Set.objects.create(exercise_id=ex_id, user=user, e1rm_kg=rm, logged_at=logged_at, **validated_data)
        
class PRSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(many=False, read_only=True)
    exercise_id = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(),
        source="exercise",
        write_only=True
    )

    class Meta:
        model = PR
        fields = [
            "id",
            "user",
            "bodyweight_kg",
            "exercise_id",
            "exercise",
            "weight_kg",
            "reps",
            "e1rm_kg",
            "achieved_at",
            "source_set",
            "status",
            "invalidation_reason",
            "invalidated_at",
            "beaten_by"
        ]

        read_only_fields = [
            "user_id",
            "exercise_id",
        ]


class StrengthStandardSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrengthStandard
        fields = [
            "id",
            "exercise",
            "level",
            "bw_multiplier",
            "sex"
        ]

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "user",
            "bodyweight_kg",
            "preferred_unit",
            "sex"
        ]

class MuscleStrengthIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = MuscleStrengthIndicator
        fields = [
            "exercise",
            "muscle_group",
            "indicator_weight"
        ]

class ExerciseStrengthEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseStrengthEvaluation
        fields = [
            "id",
            "user",
            "exercise",
            "pr",
            "strength_level",
            "level_progress",
            "next_level",
            "score",
            "evaluated_at"
        ]