from ..models import Workout, Set, PR, PRStatus
from django.db.models import Count, Sum, F, ExpressionWrapper, DecimalField, Q
from django.db.models.functions import Coalesce
from django.db.models import Exists, OuterRef
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
    all_sets = (
        Set
        .objects
        .filter(user=user)
        .filter(logged_at__lte=end_date, logged_at__gte=start_date)
        .annotate(
            exercise_name=F("exercise__name"),
            primary_muscle=F("exercise__primary_muscle"),
            is_compound=F("exercise__is_compound"),
            is_new_pr=Exists(PR.objects.filter(set=OuterRef("id"))),
        )
    )

    count_new_prs = 









    










