from django.contrib import admin
from .models import Workout, Set, Exercise, ExerciseSecondaryMuscle

admin.site.register(Workout)
admin.site.register(Exercise)
admin.site.register(Set)
admin.site.register(ExerciseSecondaryMuscle)

