from ..models import Set, PR, PRInvalidationReason, PRStatus, Exercise
from ..utils import get_past_dt
from django.utils import timezone
from decimal import Decimal
from .strength_evaluations import update_exercise_strength_evaluation
from ..exceptions import StrengthEvaluationUpdateError
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from django.conf import settings
from collections import Counter



def handle_new_set(set_instance: Set):
    reps = set_instance.reps

    if reps > 8:
        return None

    user = set_instance.user
    exercise = set_instance.exercise
    e1rm = set_instance.e1rm_kg

    with transaction.atomic():

        existing_pr = (
            PR.objects
            .select_for_update()
            .filter(
                user=user,
                exercise=exercise,
                status=PRStatus.ACTIVE
            )
            .first()
        )

        if existing_pr is None or existing_pr.e1rm_kg < e1rm:

            bodyweight_kg = user.profile.bodyweight_kg
            achieved_at = set_instance.logged_at

            if existing_pr:
                invalidate_beaten_pr(
                    beaten_pr=existing_pr,
                    invalidated_at=achieved_at
                )

                existing_pr.save(update_fields=[
                    "status",
                    "invalidation_reason",
                    "invalidated_at",
                ])

            new_pr = create_new_pr(
                user=user,
                bodyweight_kg=bodyweight_kg,
                source_set=set_instance,
                exercise=exercise,
                weight_kg=set_instance.weight_kg,
                reps=reps,
                e1rm_kg=e1rm,
                achieved_at=achieved_at
            )

            if existing_pr:
                existing_pr.beaten_by = new_pr
                existing_pr.save(update_fields=["beaten_by"])

            strength_eval_data = update_exercise_strength_evaluation(
                pr_instance=new_pr,
                exercise=exercise,
                user=user,
                bodyweight_kg=bodyweight_kg,
                e1rm=e1rm
            )

            return {
                "exercise_strength_evaluation_event": strength_eval_data,
                "pr_event": {
                    "ACTION": "CREATE",
                    "estimated_1_rep_max": e1rm,
                }
            }

    return None

def handle_set_deleted(set_instance):
    try:
        pr = set_instance.pr
    except PR.DoesNotExist:
        pr = None
    
    exercise = set_instance.exercise
    user = set_instance.user
    bodyweight_kg = user.profile.bodyweight_kg

    if pr:
        with transaction.atomic():
            set_instance.delete()

            cutoff = get_past_dt(weeks=settings.PR_EXPIRATION_WEEKS)
            new_pr_set = (
                Set
                .objects
                .filter(
                    user=user,
                    exercise=exercise,
                    logged_at__gt=cutoff
                )
                .order_by("-e1rm_kg", "-logged_at")
            ).first()

            if new_pr_set is None:
                return None 
            
            try:
                invalidated_pr = new_pr_set.pr
            except PR.DoesNotExist:
                invalidated_pr = None


            if invalidated_pr:
                invalidated_pr.status = PRStatus.ACTIVE
                invalidated_pr.invalidated_at = None
                invalidated_pr.invalidation_reason = None
                invalidated_pr.beaten_by = None
                invalidated_pr.save()

                e1rm = invalidated_pr.e1rm_kg

                strength_eval_data = update_exercise_strength_evaluation(
                    pr_instance=invalidated_pr, exercise=exercise, 
                    user=user, bodyweight_kg=bodyweight_kg, e1rm=e1rm
                )

                return {
                    "exercise_strength_evaluation_event": strength_eval_data,
                    "pr_event": {
                        "ACTION": "RESTORED",
                        "estimated_1_rep_max": e1rm
                    }
                }


            else:
                weight_kg = new_pr_set.weight_kg
                reps = new_pr_set.reps
                e1rm = new_pr_set.e1rm_kg
                achieved_at = new_pr_set.logged_at

                new_pr = create_new_pr(
                    user=user,
                    bodyweight_kg=bodyweight_kg,
                    source_set=new_pr_set,
                    exercise=exercise,
                    weight_kg=weight_kg,
                    reps=reps,
                    e1rm_kg=e1rm,
                    achieved_at=achieved_at
                )

                strength_eval_data = update_exercise_strength_evaluation(
                    pr_instance=new_pr, exercise=exercise, 
                    user=user, bodyweight_kg=bodyweight_kg, 
                    e1rm=e1rm
                )
            
                return {
                    "exercise_strength_evaluation_event": strength_eval_data,
                    "pr_event": {
                        "ACTION": "CREATE",
                        "estimated_1_rep_max": e1rm,
                    }
                }
    
    set_instance.delete()
    return None



def invalidate_expired_prs(batch_size):
    cutoff = get_past_dt(weeks=settings.PR_EXPIRATION_WEEKS)
    expired_PRs_ids = list(
        PR
        .objects
        .filter(
            status=PRStatus.ACTIVE,
            achieved_at__lte=cutoff
        )
        .order_by("achieved_at")
        .values_list("id", flat=True)[:batch_size]
    )
    print("expired_prs: ")
    for expired in expired_PRs_ids:
        print(expired)

    stats = Counter()
    stats["candidates"] = len(expired_PRs_ids)

    for expired_pr_id in expired_PRs_ids:

        try:
            result = process_one_expired_PR(expired_pr_id, cutoff)
        except IntegrityError:
            stats["race_conflicts"] += 1
            continue
        except Exception:
            stats["errors"] += 1
            continue

        if result is None:
            stats["skipped"] += 1
        else:
            stats[result["action"]] += 1
        
    return dict(stats)
        
            
def process_one_expired_PR(pr_id, cutoff):
    with transaction.atomic():
        expired_pr = (
            PR
            .objects
            .select_for_update()
            .select_related("user", "exercise")
            .filter(
                id=pr_id,
                status=PRStatus.ACTIVE,
                achieved_at__lte=cutoff
            )
        ).first()

        if expired_pr is None:
            return None
        
        user = expired_pr.user
        exercise = expired_pr.exercise
        bodyweight_kg = user.profile.bodyweight_kg

        expired_pr.status = PRStatus.INVALIDATED
        expired_pr.invalidation_reason = PRInvalidationReason.EXPIRED
        expired_pr.invalidated_at = timezone.now()

        expired_pr.save(update_fields=["status", "invalidation_reason", "invalidated_at"])

        replacement_set = (
            Set
            .objects
            .select_for_update()
            .filter(
                user=user,
                exercise=exercise,
                reps__lte=8,
                logged_at__gt=cutoff
            )
            .order_by("-e1rm_kg", "-logged_at")
            .first()
        )

        if replacement_set is None:
            return {"action": "expired_no_replacement"}
        
        try:
            replacement_pr = replacement_set.pr
        except PR.DoesNotExist:
            try:
                replacement_pr = PR.objects.create(
                    user=user,
                    bodyweight_kg=bodyweight_kg,
                    source_set=replacement_set,
                    exercise=exercise,
                    weight_kg=replacement_set.weight_kg,
                    reps=replacement_set.reps,
                    e1rm_kg=replacement_set.e1rm_kg,
                    achieved_at=replacement_set.logged_at,
                    status=PRStatus.ACTIVE
                )
            except IntegrityError:
                # New Active PR created during the transaction, roll back and clean up
                raise
        else:
            replacement_pr.status = PRStatus.ACTIVE
            replacement_pr.invalidated_at = None
            replacement_pr.invalidation_reason = None
            replacement_pr.beaten_by = None
            replacement_pr.save(update_fields=["status", "invalidated_at", "invalidation_reason", "beaten_by"])

        update_exercise_strength_evaluation(
            pr_instance=replacement_pr,
            exercise=exercise,
            user=user,
            bodyweight_kg=bodyweight_kg,
            e1rm=replacement_pr.e1rm_kg
        )

        return {"action": "expired_replaced"}


def get_pr(user, exercise) -> PR:
    pr = (
        PR
        .objects
        .filter(
            user=user,
            exercise=exercise,
            status=PRStatus.ACTIVE
        )
    ).first()

    return pr

def invalidate_beaten_pr(beaten_pr: PR, invalidated_at) -> None:
    beaten_pr.status = PRStatus.INVALIDATED
    beaten_pr.invalidation_reason = PRInvalidationReason.BEATEN
    beaten_pr.invalidated_at = invalidated_at


def create_new_pr(
        user: User, 
        bodyweight_kg: Decimal,
        source_set: Set, 
        exercise: Exercise, 
        weight_kg: Decimal, 
        reps: int, 
        e1rm_kg: Decimal, 
        achieved_at,
        status=PRStatus.ACTIVE,
        beaten_by=None,
        invalidation_reason=None,
        invalidated_at=None,
    ) -> PR:
    
    new_pr = PR.objects.create(
        user=user,
        bodyweight_kg=bodyweight_kg,
        source_set=source_set,
        exercise=exercise,
        weight_kg=weight_kg,
        reps=reps,
        e1rm_kg=e1rm_kg,
        achieved_at=achieved_at,
        status=status,
        beaten_by=beaten_by,
        invalidation_reason=invalidation_reason,
        invalidated_at=invalidated_at
    )
    
    return new_pr
    

