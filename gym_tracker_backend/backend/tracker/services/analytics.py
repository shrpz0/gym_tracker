from ..models import Workout, Set, PR, PRStatus, Region, MovementPattern
from django.db.models import Count, Sum, F, ExpressionWrapper, DecimalField, Q
from django.db.models.functions import Coalesce
from django.db.models import Exists, OuterRef
from decimal import Decimal
from ..utils import safe_ratio
from collections import defaultdict

### Review focusing mostly on analytics, returns:
    # Number of total sets
    # Number of lower body and upper body sets and their ratio
    # Number of push / pull sets and their ratio
    # Number of upper push / upper pull and their ratio
    # Number of compound lifts
    # Number of sets per muscle group
    # The most and least worked muscles
# To add later on: New PRs hit this week, overtraining alerts, undertraining alerts


def get_stats(start_dt, end_dt, user):

    
    base_filter = Q(user=user, logged_at__gt=start_dt, logged_at__lte=end_dt)
    is_pr_annotation = Exists(PR.objects.filter(source_set=OuterRef("id")))


    aggregate = (
        Set
        .objects
        .filter(base_filter)
        .annotate(is_pr=is_pr_annotation)
        .aggregate(
            sets_count = Count("id"),
            upper_sets_count = Count("id", filter=Q(exercise__region=Region.UPPER)),
            lower_sets_count = Count("id", filter=Q(exercise__region=Region.LOWER)),
            full_body_sets_count = Count("id", filter=Q(exercise__region=Region.FULL)),
            compound_sets_count = Count("id", filter=Q(exercise__is_compound=True)),
            bodyweight_sets_count = Count("id", filter=Q(exercise__is_bodyweight=True)),
            hard_sets_count = Count("id", filter=Q(rir__lte=1)),
            new_prs_count = Count("id", filter=Q(is_pr=True))
        )
    )


    sets_count = aggregate["sets_count"]
    upper_sets_count = aggregate["upper_sets_count"]
    lower_sets_count = aggregate["lower_sets_count"]
    full_body_sets_count = aggregate["full_body_sets_count"]
    compound_sets_count = aggregate["compound_sets_count"]
    bodyweight_sets_count = aggregate["bodyweight_sets_count"]
    hard_sets_count = aggregate["hard_sets_count"]
    new_prs_count = aggregate["new_prs_count"]


    upper_ratio_all = safe_ratio(upper_sets_count, sets_count)
    lower_ratio_all = safe_ratio(lower_sets_count, sets_count)
    full_body_ratio = safe_ratio(full_body_sets_count, sets_count)
    compound_sets_ratio = safe_ratio(compound_sets_count, sets_count)
    bodyweight_sets_ratio = safe_ratio(bodyweight_sets_count, sets_count)
    hard_sets_ratio = safe_ratio(hard_sets_count, sets_count)

    upper_ratio = safe_ratio(upper_sets_count, (upper_sets_count + lower_sets_count))
    lower_ratio = safe_ratio(lower_sets_count, (upper_sets_count + lower_sets_count))
    
    per_exercise = list(
        Set
        .objects
        .filter(base_filter)
        .annotate(is_pr=is_pr_annotation)
        .values("exercise__name", "exercise__primary_muscle")
        .annotate(
            pr_count=Count("id", filter=Q(is_pr=True)),
            sets_count=Count("id")
        )
        .order_by("-sets_count")
    )

    three_most_performed_ex = per_exercise[:3]
    
    mg_sets = defaultdict(int)
    for row in per_exercise:
        mg_sets[row["exercise__primary_muscle"]] += row["sets_count"]
    

    mg_sorted = sorted(mg_sets.items(), key=lambda x:x[1], reverse=True)
    most_worked_mg = mg_sorted[:3]
    least_worked_mg = mg_sorted[-3:]

    return {
        "summary": {
            "sets_count": sets_count,
            "upper_sets_count": upper_sets_count,
            "lower_sets_count": lower_sets_count,
            "full_body_sets_count": full_body_sets_count,
            "bodyweight_sets_count": bodyweight_sets_count,
            "compound_sets_count": compound_sets_count,
            "hard_sets_count": hard_sets_count,
            "new_prs_count": new_prs_count,
        },
        "ratios": {
            "upper_ratio_all": upper_ratio_all,
            "lower_ratio_all": lower_ratio_all,
            "full_body_ratio": full_body_ratio,
            "bodyweight_sets_ratio": bodyweight_sets_ratio,
            "compound_sets_ratio": compound_sets_ratio,
            "hard_sets_ratio": hard_sets_ratio,
            "upper_ratio": upper_ratio,
            "lower_ratio": lower_ratio,
        },
        "top_exercises": three_most_performed_ex,
        "muscle_groups": {
            "most_worked": [
                {"muscle": muscle, "sets_count": count}
                for muscle, count in most_worked_mg
            ],
            "least_worked": [
                {"muscle": muscle, "sets_count": count}
                for muscle, count in least_worked_mg
            ],
        },
}


    









    










