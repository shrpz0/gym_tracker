from .models import Workout, Set
from django.db.models import Count, Sum, F, ExpressionWrapper, DecimalField
from .utils import safe_ratio

### Review focusing mostly on analytics, returns:
    # Number of total sets
    # Number of lower body and upper body sets and their ratio
    # Number of push / pull sets and their ratio
    # Number of lower push / lower pull and their ratio
    # Number of upper push / lower pull and their ratio
    # Number of compound lifts
    # Number of sets per muscle group
    # The most and least worked muscles
# To add later on: New PRs hit this week, overtraining alerts, undertraining alerts

def get_review(start_date, end_date, user):

    ### All sets
    qs = (
        Set
        .objects
        .filter(user=user)
        .filter(workout__logged_at__gte=start_date, workout__logged_at__lt=end_date)
    )

    upper_sets = qs.filter(region="UPPER")
    lower_sets = qs.filter(region="LOWER")
    full_body_sets = qs.filter(region="FULL")
    compound_sets = qs.filter(is_compound=True)

    ### Number of sets across all workouts
    n_sets = qs.count()

    ### Number of compound sets
    n_compound = compound_sets.count()

    ### Number of sets per region
    n_upper_sets = upper_sets.count()
    n_lower_sets = lower_sets.count()
    n_full_body_sets = full_body_sets.count()

    ### Upper and lower ratio distribution - excluding full body sets
    upper_ratio = round(n_upper_sets / (n_upper_sets + n_lower_sets), 1)
    lower_ratio = 1 - lower_ratio

    ### Upper, lower, full body sets ratio distribution 
    upper_all_ratio = safe_ratio
    lower_all_ratio = round(n_lower_sets / n_sets, 1)
    full_body_all_ratio = round(n_full_body_sets / n_sets, 1)

    ### Compound sets ratio distribution 
    compound_distribution = round(n_compound / n_sets, 1)

    ### Total reps n volume across all sets
    reps_n_volume = qs.aggregate(
        total_reps=Sum("reps"), 
        total_volume=Sum(
            ExpressionWrapper(
                F("reps") * F("weight_kg"), 
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )
    )
    n_reps = reps_n_volume.get("total_reps", 0)
    volume = reps_n_volume.get("total_volume", 0)



    










