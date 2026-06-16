from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from .utils import round_decimal
from django.conf import settings


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
    VERTICAL_PUSH = "VERTICAL_PUSH", "Vertical Push"
    HORIZONTAL_PUSH = "HORIZONTAL_PUSH", "Horizontal Push"

    VERTICAL_PULL = "VERTICAL_PULL", "Vertical Pull"
    HORIZONTAL_PULL = "HORIZONTAL_PULL", "Horizontal Pull"

    SQUAT = "SQUAT", "Squat"
    HINGE = "HINGE", "Hinge"

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

class PRResultConfidence(models.TextChoices):
    HIGH = "HIGH", "High"
    MEDIUM = "MEDIUM", "Medium"
    LOW = "LOW", "Low"

class PRMetric(models.TextChoices):
    E1RM = "E1RM", "Estimated 1RM"
    REPS = "REPS", "Reps"


LEVEL_TO_NUM = {
    StrengthLevel.BEGINNER : 1,
    StrengthLevel.NOVICE : 2,
    StrengthLevel.INTERMEDIATE : 3,
    StrengthLevel.ADVANCED : 4,
    StrengthLevel.ELITE : 5
}


class Sex(models.TextChoices):
    M = "M", "Male"
    F = "F", "Female"

class PRInvalidationReason(models.TextChoices):
    EXPIRED = "EXPIRED", "Expired"
    BEATEN = "BEATEN", "Beaten"

class PRStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INVALIDATED = "INVALIDATED", "Invalidated"



class Exercise(models.Model):
    name = models.CharField(max_length=50, unique=True)
    primary_muscle = models.CharField(max_length=15, choices=MuscleGroup.choices)
    secondary_muscles = models.ManyToManyField(
            "ExerciseSecondaryMuscle",
            through="ExerciseSecondaryLink",
            related_name="exercises",
            blank=True,
    )

    pattern = models.CharField(max_length=15, choices=MovementPattern.choices)
    region = models.CharField(max_length=10, choices=Region.choices)
    is_compound = models.BooleanField(default=True)
    is_bodyweight = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=["pattern", "region"])
        ]

    def __str__(self):
        return self.name
    

class MuscleStrengthIndicator(models.Model):
    muscle_group = models.CharField(max_length=15, choices=MuscleGroup.choices)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="muslce_strength_indicators")
    indicator_weight = models.DecimalField(decimal_places=2, max_digits=4, default=Decimal("1.00"))


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
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="strength_standards")
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
        return f"{self.user.username} - {self.logged_at.date()}"
    


class Set(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name="sets")
    is_bodyweight = models.BooleanField(default=False)
    logged_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    reps = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(200)])
    weight = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, editable=False)
    unit = models.CharField(max_length=2, choices=WeightUnit.choices, default=WeightUnit.KG)
    rir = models.PositiveSmallIntegerField(null=True, blank=True)
    e1rm_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="sets")

    def save(self, *args, **kwargs):

        if self.unit == WeightUnit.LB:
            self.weight_kg = round_decimal(self.weight * LB_TO_KG)

        elif self.unit == WeightUnit.KG:
            self.weight_kg = self.weight
        else:
            raise ValueError("Unsuported Unit")
        
        return super().save(*args, **kwargs)
    

    class Meta:
        indexes = [
            models.Index(fields=["workout", "exercise"]),
        ]


class PR(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="prs")
    bodyweight_kg = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(25), MaxValueValidator(500)])
    source_set = models.OneToOneField(Set, on_delete=models.CASCADE, related_name="pr")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, unique=False, related_name="prs")
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    reps = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(200)])

    e1rm_kg = models.DecimalField(
        max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], 
        null=True, blank=True
    )

    achieved_at = models.DateTimeField(default=timezone.now, null=False)

    status = models.CharField(choices=PRStatus.choices, default=PRStatus.ACTIVE)
    invalidation_reason = models.CharField(choices=PRInvalidationReason.choices, default=None, null=True, blank=True)
    invalidated_at = models.DateTimeField(default=None, null=True, blank=True)
    beaten_by = models.OneToOneField("self", default=None, null=True, blank=True, on_delete=models.SET_NULL, related_name="beaten_pr")

    pr_metric = models.CharField(max_length=4, choices=PRMetric.choices, default=PRMetric.E1RM)

    def achieved_weeks_ago(self):
        delta = timezone.now() - self.achieved_at
        return delta.days // 7
    
    def is_expired(self):
        return self.achieved_weeks_ago() >= settings.PR_EXPIRATION_WEEKS
    

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "exercise"],
                condition=models.Q(status="ACTIVE"),
                name="unique_active_pr_per_user_exercise"
            )
        ]
        indexes = [
            models.Index(fields=["user", "exercise"]),
            models.Index(fields=["achieved_at"])
        ]



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    sex = models.CharField(max_length=1, choices=Sex.choices)
    bodyweight_kg = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(25), MaxValueValidator(500)])
    preferred_unit = models.CharField(max_length=2, choices=WeightUnit.choices, default=WeightUnit.KG)

class ExerciseStrengthEvaluation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="strength_evaluations")
    bodyweight_kg = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(25), MaxValueValidator(500)])
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="strength_evaluations")
    pr = models.OneToOneField(PR, on_delete=models.CASCADE, related_name="strength_evaluation")
    strength_level = models.CharField(max_length=12, choices=StrengthLevel.choices)
    level_progress = models.DecimalField(max_digits=3, decimal_places=2)
    score = models.DecimalField(max_digits=3, decimal_places=2, editable=False)
    next_level = models.CharField(max_length=12, choices=StrengthLevel.choices)
    evaluated_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        self.score = self.strength_level_decimal() + self.level_progress
        return super().save(*args, **kwargs)
    
    def strength_level_decimal(self):
        return Decimal(LEVEL_TO_NUM[self.strength_level])
    
    class Meta:
        unique_together = [("user", "exercise")]
        indexes = [models.Index(fields=["user", "exercise"])]


### For invalidating
## ON PRs GET:
#       -use a replace_expired_prs function (to replace all expired prs) -> .filter(achieved_at__lt=cutoff) -> for each, replace_pr function 
# ON StrengthProfile GET:
#   -Strength Profile fetches PRs for strength indicative exercises -> Check with .is_expired() -> If yes -> replace_expired_pr (to replace a particular expired pr)
