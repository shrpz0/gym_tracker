from ..models import Set, PR, MuscleStrengthIndicator, Exercise, ExerciseStrengthEvaluation
from decimal import Decimal
from ..utils import get_past_dt, get_median_value, round_decimal
from django.db.models import Prefetch, F, ExpressionWrapper, Value, OuterRef, Subquery, DecimalField, Count
from django.db.models.functions import Coalesce



#Goal:
#Compute a realistic, current strength profile per muscle group using:
#   -PR-based strength evaluations
#   -Exercise importance weighting
#   -Outlier filtering (to ignore garbage data)

# Compute a confidence score of the result:
#   -Coverage confidence (How many indicative exercises does the user have valid data for?)
#   -Exercise intrinsic confidence (Some exercises are better indicators than others)
#   - Sample size confidence (How much recent data exists for that specific exercise?)


def get_strength_profile(user_id):
    """Compute realistic strength profile per muscle group.."""
    indicators_evals_qs = get_indicators_and_evals(user_id=user_id)

    muscle_groups = {}
    sum_weights = Decimal(0)
    sum_used_weights = Decimal(0)
    all_performed_ex_ids = set()
    all_unperformed_ex_ids = set()

    # First pass: group data and calculate global coverage
    for x in indicators_evals_qs:
        mg = x.muscle_group
        w = x.indicator_weight
        score = x.evaluation_score
        ex_id = x.exercise_id

        if mg not in muscle_groups:
            muscle_groups[mg] = {
                "exercises": [],           # Only performed ones with scores
                "sum_mg_weights": Decimal(0),
                "sum_mg_used_weights": Decimal(0),
            }

        muscle_groups[mg]["sum_mg_weights"] += w
        sum_weights += w

        if score is not None: 
            muscle_groups[mg]["exercises"].append({
                "score": score,
                "weight": w,
                "ex_id": ex_id
            })
            muscle_groups[mg]["sum_mg_used_weights"] += w
            sum_used_weights += w
            all_performed_ex_ids.add(ex_id)
        else:
            all_unperformed_ex_ids.add(ex_id)

    global_coverage_confidence = round_decimal(sum_used_weights / sum_weights) if sum_weights > 0 else Decimal(0)

    results = {
        "global_coverage_confidence": global_coverage_confidence
    }

    # Fetch set counts for sample size confidence (only performed exercises)
    performed_exercises_set_counts = get_exercises_set_counts(
        user_id=user_id, 
        exercises=all_performed_ex_ids
    )

    # Second pass: calculate per muscle group scores with outlier filtering
    for mg, mg_data in muscle_groups.items():
        # Extract scores for median calculation
        scores = [ex["score"] for ex in mg_data["exercises"]]
        scores_median = get_median_value(sorted_values=scores) if scores else Decimal(0)
        outlier_threshold = max(Decimal(1), scores_median * Decimal("0.35"))

        user_score = Decimal(0)
        max_score = Decimal(0)

        sum_sample_size_confidence = Decimal(0)
        max_sample_size_confidence = Decimal(0)

        for ex in mg_data["exercises"]:
            w = ex["weight"]
            score = ex["score"]
            ex_id = ex["ex_id"]

            # Sample size confidence (capped at 12 sets)
            ex_set_count = Decimal(min(12, performed_exercises_set_counts.get(ex_id, 0)))
            sum_sample_size_confidence += round_decimal((ex_set_count / Decimal("12.00")) * w)
            max_sample_size_confidence += round_decimal(Decimal("1.00") * w)

            # Outlier filtering
            if scores_median - score < outlier_threshold:
                user_score += score * w
                max_score += Decimal("5.00") * w

        # Final muscle group metrics
        mg_score = round_decimal((user_score / max_score) * Decimal("5.00")) if max_score > 0 else Decimal(0)
        mg_sample_conf = round_decimal(sum_sample_size_confidence / max_sample_size_confidence) if max_sample_size_confidence > 0 else Decimal(0)
        mg_coverage_conf = round_decimal(
            mg_data["sum_mg_used_weights"] / mg_data["sum_mg_weights"]
        ) if mg_data["sum_mg_weights"] > 0 else Decimal(0)

        results[mg] = {
            "score": mg_score,
            "sample_size_confidence": mg_sample_conf,
            "coverage_confidence": mg_coverage_conf,
        }

    return results



def get_indicators_and_evals(user_id):
    """Get all muscle indicators with latest evaluation scores via subquery."""
    evaluation_subq = (
        ExerciseStrengthEvaluation
        .objects
        .filter(user=user_id)
        .filter(exercise_id=OuterRef("exercise_id"))
        .values("score")[:1]
    )

    return (
        MuscleStrengthIndicator
        .objects
        .annotate(evaluation_score=Subquery(evaluation_subq, output_field=DecimalField(max_digits=3, decimal_places=2)))
        .order_by("-evaluation_score")
    )


def get_exercises_set_counts(user_id, exercises, cutoff=get_past_dt(weeks=8)):
    """Count recent sets per exercise for sample size confidence."""
    if not exercises:
        return {}

    qs = (
        Set.objects
        .filter(workout__user=user_id)
        .filter(exercise_id__in=exercises)
        .filter(workout__logged_at__gt=cutoff)
        .values("exercise_id")
        .annotate(set_count=Count("id"))
    )

    return {item["exercise_id"]: item["set_count"] for item in qs}