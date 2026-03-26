from ..models import Workout, Set
from django.db.models import Count, Sum, F, ExpressionWrapper, DecimalField, Q
from django.db.models.functions import Coalesce
from decimal import Decimal
from ..utils import safe_ratio

### Review focusing mostly on analytics, returns:
    # Number of total sets
    # Number of lower body and upper body sets and their ratio
    # Number of push / pull sets and their ratio
    # Number of upper push / upper pull and their ratio
    # Number of compound lifts
    # Number of sets per muscle group
    # The most and least worked muscles
# To add later on: New PRs hit this week, overtraining alerts, undertraining alerts


def get_review(start_date, end_date, user):
    ### All sets
    qs = (
        Set
        .objects
        .filter(workout__user=user)
        .filter(workout__logged_at__gte=start_date, workout__logged_at__lt=end_date)
    )

    sets_n = qs.aggregate(
        n_sets=Count("id"),
        n_workouts = Count("workout", distinct=True),
        n_upper_sets=Count("id", filter=Q(exercise__region="UPPER")),
        n_lower_sets=Count("id", filter=Q(exercise__region="LOWER")),
        n_full_body_sets=Count("id", filter=Q(exercise__region="FULL")),
        n_compound_sets=Count("id", filter=Q(exercise__is_compound=True)),

        n_upper_pull=Count("id", filter=(Q(exercise__pattern="PULL") & Q(exercise__region="UPPER"))),
        n_upper_push=Count("id", filter=(Q(exercise__pattern="PUSH") & Q(exercise__region="UPPER"))),

        n_strength_sets=Count("id", filter=Q(reps__lte=6)),
        n_hypertrophy_sets=Count("id", filter=Q(reps__range=(7, 12))),
        n_endurance_sets=Count("id", filter=Q(reps__gt=12)),
    )

    ### Number of Workouts
    n_workouts = sets_n["n_workouts"]

    ### Number of total sets
    n_sets = sets_n["n_sets"]

    ### Number of compound sets
    n_compound = sets_n["n_compound_sets"]

    ### Number of sets per region
    n_upper_sets = sets_n["n_upper_sets"]
    n_lower_sets = sets_n["n_lower_sets"]
    n_full_body_sets = sets_n["n_full_body_sets"]

    ### Number of sets per pattern
    n_upper_pull = sets_n["n_upper_pull"]
    n_upper_push = sets_n["n_upper_push"]

    n_strength_sets = sets_n["n_strength_sets"]
    n_hypertrophy_sets = sets_n["n_hypertrophy_sets"]
    n_endurance_sets = sets_n["n_endurance_sets"]


    ### Upper and lower ratio distribution - excluding full body sets
    upper_ratio = safe_ratio(n_upper_sets, (n_upper_sets + n_lower_sets))
    lower_ratio = round(1 - upper_ratio, 3) if n_lower_sets > 0 else 0

    ### Upper, lower, full body sets ratio distribution 
    upper_all_ratio = safe_ratio(n_upper_sets, n_sets)
    lower_all_ratio = safe_ratio(n_lower_sets, n_sets)
    full_body_all_ratio = safe_ratio(n_full_body_sets, n_sets)

    ### Compound sets ratio distribution 
    compound_ratio = safe_ratio(n_compound, n_sets)


    ### Total reps n volume across all sets
    reps_n_volume = qs.aggregate(
        total_reps=Coalesce(Sum("reps"), 0), 
        total_volume=Coalesce(Sum(
            ExpressionWrapper(
                F("reps") * F("weight_kg"), 
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        ), Decimal("0.00"))
    )

    sets_per_muscle_group = qs.values("exercise__primary_muscle").annotate(number_of_sets=Count("id"))

    n_reps = reps_n_volume.get("total_reps", 0)
    volume = reps_n_volume.get("total_volume", 0)


    ### RETURN DICTIONARY
    return {
        "n_workouts": n_workouts,
        "n_sets": n_sets,
        "n_compound_sets": n_compound,

        "n_upper_sets": n_upper_sets,
        "n_lower_sets": n_lower_sets,
        "n_full_body_sets": n_full_body_sets,

        "n_upper_pull": n_upper_pull,
        "n_upper_push": n_upper_push,

        "n_strength_sets": n_strength_sets,
        "n_hypertrophy_sets": n_hypertrophy_sets,
        "n_endurance_sets": n_endurance_sets,

        "upper_ratio": upper_ratio,
        "lower_ratio": lower_ratio,

        "upper_all_ratio": upper_all_ratio,
        "lower_all_ratio": lower_all_ratio,
        "full_body_all_ratio": full_body_all_ratio,

        "compound_ratio": compound_ratio,

        "total_reps": n_reps,
        "total_volume": volume,

        "sets_per_muscle_group": list(sets_per_muscle_group),
    }







    










