from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


LB_TO_KG = Decimal("0.45359237")

class MuscleGroup(models.TextChoices):
    CHEST = "CHEST", "Chest"
    BACK = "BACK", "Back"
    BICEPS = "BICEPS", "Biceps"
    TRICEPS = "TRICEPS", "Triceps"
    SHOULDERS = "SHOULDERS", "Shoulders"
    CORE = "CORE", "Core"
    QUADS = "QUADS", "Quads"
    HAMSTRINGS = "HAMSTRINGS", "Hamstrings"
    GLUTES = "GLUTES", "Glutes"
    CALVES = "CALVES", "Calves"
    NECK = "NECK", "Neck"
    FOREARMS = "FOREARMS", "Forearms"


class MovementPattern(models.TextChoices):
    PUSH = "PUSH", "Push"
    PULL = "PULL", "Pull"
    SQUAT = "SQUAT", "Squat pattern"
    HINGE = "HINGE", "Hinge pattern"
    CARRY = "CARRY", "Carry"
    CORE = "CORE", "Core"
    OTHER = "OTHER", "Other"

class Region(models.TextChoices):
    UPPER = "UPPER", "Upper"
    LOWER = "LOWER", "Lower"
    FULL = "FULL", "Full body"

class WeightUnit(models.TextChoices):
    KG = "KG", "kg"
    LB = "LB", "lb"

class StrengthLevel(models.TextChoices):
    BEGINNER = "BEGINNER", "Beginner"
    NOVICE = "NOVICE", "Novice"
    INTERMEDIATE = "INTERMEDIATE", "Intermediate"
    ADVANCED = "ADVANCED", "Advanced"
    ELITE = "ELITE", "Elite"

class Sex(models.TextChoices):
    M = "M", "Male"
    F = "F", "Female"

class PRType(models.TextChoices):
    ESTIMATED = "ESTIMATED", "Estimated"
    ACTUAL = "ACTUAL", "Actual"


class Exercise(models.Model):
    name = models.CharField(max_length=30, unique=True)
    primary_muscle = models.CharField(max_length=15, choices=MuscleGroup.choices)
    secondary_muscles = models.ManyToManyField(
            "ExerciseSecondaryMuscle",
            through="ExerciseSecondaryLink",
            related_name="exercises",
            blank=True,
    )

    pattern = models.CharField(max_length=10, choices=MovementPattern.choices)
    region = models.CharField(max_length=10, choices=Region.choices)
    is_compound = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["pattern", "region"])
        ]

    def __str__(self):
        return self.name
    

class ExerciseSecondaryMuscle(models.Model):
    muscle_group = models.CharField(max_length=15, choices=MuscleGroup.choices, unique=True)
    def __str__(self):
        return self.muscle_group

class ExerciseSecondaryLink(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    secondary = models.ForeignKey(ExerciseSecondaryMuscle, on_delete=models.CASCADE)

    class Meta:
        unique_together = [("exercise", "secondary")]
    

class StrengthStandard(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    level = models.CharField(max_length=15, choices=StrengthLevel.choices)
    
    bw_multiplier = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0)])
    sex = models.CharField(max_length=1, choices=Sex.choices)

    class Meta:
        unique_together = [("exercise", "level", "sex")]
        indexes = [models.Index(fields=["exercise", "level", "sex"])]



class Workout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workouts")
    logged_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    note = models.TextField(max_length=2000, null=True, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)])

    class Meta:
        indexes = [
            models.Index(fields=["user", "logged_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.logged_at}"
    


class Set(models.Model):

    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    reps = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(200)])
    weight = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, editable=False)
    unit = models.CharField(max_length=2, choices=WeightUnit.choices, default=WeightUnit.KG)
    rir = models.PositiveSmallIntegerField(null=True, blank=True)
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="sets")

    def save(self, *args, **kwargs):
        if self.unit == WeightUnit.LB:
            self.weight_kg = self.weight * LB_TO_KG
        elif self.unit == WeightUnit.KG:
            self.weight_kg = self.weight
        else:
            raise ValueError("Unsuported Unit")
        
        return super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=["workout", "exercise"]),
        ]

class Tag(models.Model):
    name = models.CharField(max_length=50)
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="tags")


class PR(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    pr_type = models.CharField(choices=PRType.choices)
    achieved_at = models.DateField(default=timezone.now, null=False)

    class Meta:
        unique_together = ["user", "exercise", "pr_type"]

# Strength standards in relation to bodyweight to implement for exercises
# Storing user's PRs?

        