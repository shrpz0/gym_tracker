from ..models import Set, PR, PRInvalidationReason, PRStatus, PRMetric,  Exercise, Workout
from ..utils import get_past_dt
from django.utils import timezone
from decimal import Decimal
from .strength_evaluations import update_exercise_strength_evaluation
from ..exceptions import StrengthEvaluationUpdateError, InvalidPRCreationError
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from django.conf import settings
from collections import Counter
from django.db.models import F, Window
from django.db.models.functions import RowNumber
import logging

logger = logging.getLogger(__name__)



def handle_new_set(set_instance: Set):
    reps = set_instance.reps
    pr_metric = PRMetric.REPS if set_instance.is_bodyweight else PRMetric.E1RM

    if reps > 8 and pr_metric==PRMetric.E1RM:
        return None
    
    with transaction.atomic():
        user = set_instance.user
        bodyweight_kg = user.profile.bodyweight_kg
        weight_kg = set_instance.weight_kg
        e1rm = set_instance.e1rm_kg
        achieved_at = set_instance.logged_at
        exercise = set_instance.exercise

        existing_pr = (
            PR
            .objects
            .select_for_update()
            .filter(
                user=user,
                exercise=exercise,
                status=PRStatus.ACTIVE
            ).first()
        )

        if existing_pr:
            is_pr = is_new_pr(pr_metric=pr_metric, set_instance=set_instance, old_pr=existing_pr)
            if is_pr:
                existing_pr.status = PRStatus.INVALIDATED
                existing_pr.invalidation_reason = PRInvalidationReason.BEATEN
                existing_pr.invalidated_at = achieved_at
                existing_pr.save(update_fields=["status", "invalidation_reason", "invalidated_at"])
            else:
                return None

        new_pr = create_new_pr(
            user=user,
            bodyweight_kg=bodyweight_kg,
            source_set=set_instance,
            exercise=exercise,
            weight_kg=weight_kg,
            e1rm_kg=e1rm,
            reps=reps,
            pr_metric=pr_metric,
            achieved_at=achieved_at
        )
                
        if existing_pr and is_pr:
            existing_pr.beaten_by = new_pr
            existing_pr.save(update_fields=["beaten_by"])

        if pr_metric == PRMetric.E1RM:
            strength_eval_data = update_exercise_strength_evaluation(
                pr_instance=new_pr, exercise=exercise, user=user, 
                bodyweight_kg=bodyweight_kg, e1rm=e1rm
            )

            return {
                "strength_evaluation_event": strength_eval_data,
                "pr_event": {
                    "ACTION": "REPLACE" if existing_pr else "CREATE",
                    "PR_metric": pr_metric,
                    "REPS": reps,
                    "estimated_1_rep_max": new_pr.e1rm_kg,
                }
            }

            
        return {
            "pr_event": {
                "ACTION": "REPLACE" if existing_pr else "CREATE",
                "PR_metric": pr_metric,
                "REPS": reps,
                "estimated_1_rep_max": new_pr.e1rm_kg,
            }
        }


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
    
            pr_metric = pr.pr_metric
            if pr_metric == PRMetric.E1RM:
                new_pr_set = (
                    Set
                    .objects
                    .filter(
                        user=user,
                        exercise=exercise,
                        logged_at__gt=cutoff,
                        is_bodyweight=False,
                        reps__lte=8
                    )
                    .order_by("-e1rm_kg", "-logged_at")
                ).first()
            
            else:
                new_pr_set = (
                    Set
                    .objects
                    .filter(
                        user=user,
                        exercise=exercise,
                        logged_at__gt=cutoff,
                        is_bodyweight=True
                    )
                    .order_by("-reps", "-logged_at")
                ).first()

            if new_pr_set is None:
                return {
                    "exercise_strength_evaluation_event": {"ACTION": "DELETED"} if pr_metric == PRMetric.E1RM else None,
                    "pr_event": {"ACTION": "DELETED"}
                } 
            
            try:
                invalidated_pr = new_pr_set.pr
            except PR.DoesNotExist:
                invalidated_pr = None


            if invalidated_pr:
                invalidated_pr.status = PRStatus.ACTIVE
                invalidated_pr.invalidated_at = None
                invalidated_pr.invalidation_reason = None
                invalidated_pr.beaten_by = None
                invalidated_pr.save(update_fields=[
                    "status", "invalidated_at", "invalidation_reason", "beaten_by"
                ])

                e1rm = invalidated_pr.e1rm_kg
                if pr_metric == PRMetric.E1RM:
                    strength_eval_data = update_exercise_strength_evaluation(
                        pr_instance=invalidated_pr, exercise=exercise, 
                        user=user, bodyweight_kg=bodyweight_kg, e1rm=e1rm
                    )

                    return {
                        "exercise_strength_evaluation_event": strength_eval_data,
                        "pr_event": {
                            "ACTION": "RESTORED"
                        }
                    }
                else:
                    return {
                        "exercise_strength_evaluation_event": None,
                        "pr_event": {
                            "ACTION": "RESTORED"
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
                    achieved_at=achieved_at,
                    pr_metric=pr_metric
                )
            
                if pr_metric == PRMetric.E1RM:
                    strength_eval_data = update_exercise_strength_evaluation(
                        pr_instance=new_pr, exercise=exercise, 
                        user=user, bodyweight_kg=bodyweight_kg, 
                        e1rm=e1rm
                    )
            
                    return {
                        "exercise_strength_evaluation_event": strength_eval_data,
                        "pr_event": {
                            "ACTION": "CREATED",
                            "estimated_1_rep_max": e1rm,
                        }
                    }
                
                else:
                    return {
                        "exercise_strength_evaluation_event": None,
                        "pr_event": {
                            "ACTION": "RESTORED"
                        }
                    }
    
    set_instance.delete()
    return None

def handle_workout_deleted(workout_instance: Workout):

    sets_to_delete = workout_instance.sets.values_list("id", flat=True)
    user = workout_instance.user

    ### Get exercise_id of all exercises that have an active PR from this workout, to replace those PRs
    PRs_to_replace = (
        PR
        .objects
        .filter(
            source_set_id__in=sets_to_delete,
            status=PRStatus.ACTIVE,
            user=user
        ).values("exercise_id", "pr_metric")
    )
    exercise_id_reps_prs = [pr["exercise_id"] for pr in PRs_to_replace if pr["pr_metric"] == PRMetric.REPS]
    exercise_id_e1rm_prs = [pr["exercise_id"] for pr in PRs_to_replace if pr["pr_metric"] == PRMetric.E1RM]

    with transaction.atomic():
        workout_instance.delete()
        
        cutoff = get_past_dt(weeks=settings.PR_EXPIRATION_WEEKS)
        new_e1rm_pr_sets = None
        if exercise_id_e1rm_prs:
            new_e1rm_pr_sets = (
                Set
                .objects
                .filter(
                    user=user,
                    logged_at__gt=cutoff,
                    reps__lte=8,
                    is_bodyweight=False,
                    exercise_id__in=exercise_id_e1rm_prs
                )
                .annotate(
                    rk=Window(
                        expression=RowNumber(),
                        partition_by=[F("exercise_id")],
                        order_by=[F("e1rm_kg").desc(), F("logged_at").desc()]
                    )
                )
                .filter(rk=1)
            )

        new_reps_pr_sets = None
        if exercise_id_reps_prs:
            new_reps_pr_sets = (
                Set
                .objects
                .filter(
                    user=user,
                    is_bodyweight=True,
                    exercise_id__in=exercise_id_reps_prs,
                    logged_at__gt=cutoff
                )
                .annotate(
                    rk=Window(
                        expression=RowNumber(),
                        partition_by=[F("exercise_id")],
                        order_by=[F("reps").desc(), F("logged_at").desc()]
                    )
                )
                .filter(rk=1)
            )

        data = []
        if new_e1rm_pr_sets:
            for e1rm_pr_set in new_e1rm_pr_sets:

                try:
                    invalidated_pr = e1rm_pr_set.pr
                except PR.DoesNotExist:
                    invalidated_pr = None


                if invalidated_pr:
                    invalidated_pr.status = PRStatus.ACTIVE
                    invalidated_pr.invalidated_at = None
                    invalidated_pr.invalidation_reason = None
                    invalidated_pr.beaten_by = None
                    invalidated_pr.save(update_fields=[
                        "status", "invalidated_at", "invalidation_reason", "beaten_by"
                    ])

                    exercise=invalidated_pr.exercise
                    bodyweight_kg=invalidated_pr.bodyweight_kg

                    strength_eval_data = update_exercise_strength_evaluation(
                        pr_instance=invalidated_pr, exercise=exercise, 
                        user=user, bodyweight_kg=bodyweight_kg, e1rm=invalidated_pr.e1rm_kg
                    )
                
                    data.append({"ACTION": "BEATEN PR RESTORED",
                                "exercise_id": exercise.id,
                                "strength_eval_data": strength_eval_data
                                })
                    
                else:
                    weight_kg = e1rm_pr_set.weight_kg
                    reps = e1rm_pr_set.reps
                    e1rm = e1rm_pr_set.e1rm_kg
                    achieved_at = e1rm_pr_set.logged_at
                    exercise=e1rm_pr_set.exercise
                    bodyweight_kg=user.profile.bodyweight_kg

                    new_pr = create_new_pr(
                        user=user,
                        bodyweight_kg=bodyweight_kg,
                        source_set=e1rm_pr_set,
                        exercise=exercise,
                        weight_kg=weight_kg,
                        reps=reps,
                        e1rm_kg=e1rm,
                        achieved_at=achieved_at,
                        pr_metric=PRMetric.E1RM
                    )


                    strength_eval_data = update_exercise_strength_evaluation(
                        pr_instance=new_pr, exercise=exercise, 
                        user=user, bodyweight_kg=bodyweight_kg, e1rm=new_pr.e1rm_kg
                    )

                    data.append({"ACTION": "PR CREATED",
                        "exercise_id": exercise.id,
                        "strength_eval_data": strength_eval_data
                    })

        if new_reps_pr_sets:
            for reps_pr_set in new_reps_pr_sets:
                try:
                    invalidated_pr = reps_pr_set.pr
                except PR.DoesNotExist:
                    invalidated_pr = None 

                if invalidated_pr:
                    invalidated_pr.status = PRStatus.ACTIVE
                    invalidated_pr.invalidated_at = None
                    invalidated_pr.invalidation_reason = None
                    invalidated_pr.beaten_by = None
                    invalidated_pr.save(update_fields=[
                        "status", "invalidated_at", "invalidation_reason", "beaten_by"
                    ])

                    exercise = invalidated_pr.exercise
                    data.append({"ACTION": "BEATEN PR RESTORED",
                        "exercise_id": exercise.id,
                        "strength_eval_data": None
                    })

                else:
                    weight_kg = reps_pr_set.weight_kg
                    reps = reps_pr_set.reps
                    e1rm = reps_pr_set.e1rm_kg
                    achieved_at = reps_pr_set.logged_at
                    exercise_id=reps_pr_set.exercise_id
                    bodyweight_kg=user.profile.bodyweight_kg

                    new_pr = create_new_pr(
                        user=user,
                        bodyweight_kg=bodyweight_kg,
                        source_set=reps_pr_set,
                        exercise=exercise,
                        weight_kg=weight_kg,
                        reps=reps,
                        e1rm_kg=e1rm,
                        achieved_at=achieved_at,
                        pr_metric=PRMetric.REPS
                    )


                    data.append({"ACTION": "PR CREATED",
                        "exercise_id": exercise_id,
                        "strength_eval_data": None
                    })

        return data

            


    




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

    stats = Counter()
    stats["candidates"] = len(expired_PRs_ids)

    for expired_pr_id in expired_PRs_ids:
        try:
            result = process_one_expired_PR(expired_pr_id, cutoff)
        except IntegrityError:
            stats["race_conflicts"] += 1
            continue
        except Exception as e:
            logger.error(f"Task choked on PR {expired_pr_id}: {str(e)}")
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
        pr_metric = expired_pr.pr_metric

        expired_pr.status = PRStatus.INVALIDATED
        expired_pr.invalidation_reason = PRInvalidationReason.EXPIRED
        expired_pr.invalidated_at = timezone.now()

        expired_pr.save(update_fields=["status", "invalidation_reason", "invalidated_at"])

        if pr_metric == PRMetric.E1RM:
            replacement_set = (
                Set
                .objects
                .select_for_update()
                .filter(
                    user=user,
                    exercise=exercise,
                    reps__lte=8,
                    logged_at__gt=cutoff,
                    is_bodyweight=False
                )
                .order_by("-e1rm_kg", "-logged_at")
                .first()
            )
        else:
            replacement_set = (
                Set
                .objects
                .select_for_update()
                .filter(
                    user=user,
                    exercise=exercise,
                    logged_at__gt=cutoff,
                    is_bodyweight=True
                )
                .order_by("-reps", "-logged_at")
                .first()
            )

        if replacement_set is None:
            return {"action": "expired_no_replacement"}
        
        replacement_pr = create_new_pr(
            user=user,
            bodyweight_kg=bodyweight_kg,
            source_set=replacement_set,
            exercise=exercise,
            weight_kg=replacement_set.weight_kg,
            reps=replacement_set.reps,
            pr_metric=pr_metric,
            e1rm_kg=replacement_set.e1rm_kg,
            achieved_at=replacement_set.logged_at
        )
        if pr_metric == PRMetric.E1RM:
            update_exercise_strength_evaluation(
                pr_instance=replacement_pr,
                exercise=exercise,
                user=user,
                bodyweight_kg=bodyweight_kg,
                e1rm=replacement_pr.e1rm_kg
            )

        return {"action": "expired_replaced"}



def invalidate_beaten_pr(beaten_pr: PR, invalidated_at) -> None:
    beaten_pr.status = PRStatus.INVALIDATED
    beaten_pr.invalidation_reason = PRInvalidationReason.BEATEN
    beaten_pr.invalidated_at = invalidated_at


def is_new_pr(pr_metric : str, set_instance: Set, old_pr: PR):
    if pr_metric == PRMetric.REPS:
        return set_instance.reps > old_pr.reps
    elif pr_metric == PRMetric.E1RM:
        return set_instance.e1rm_kg > old_pr.e1rm_kg
    

def create_new_pr(
        user: User, 
        bodyweight_kg: Decimal,
        source_set: Set | int, 
        exercise: Exercise | int, 
        weight_kg: Decimal, 
        reps: int, 
        e1rm_kg: Decimal | None, 
        pr_metric: str,
        achieved_at,
        status=PRStatus.ACTIVE,
        beaten_by=None,
        invalidation_reason=None,
        invalidated_at=None,
    ) -> PR:

    if e1rm_kg and pr_metric == PRMetric.REPS:
        raise InvalidPRCreationError(
            message="A rep-based PR cannot have e1rm_kg.",
            code="e1rm_kg_not_allowed"
        )
    
    if weight_kg > Decimal("0.00") and pr_metric == PRMetric.REPS:
        raise InvalidPRCreationError(
            message="A rep-based PR cannot be weighted",
            code="weight_kg_not_allowed"
        )
    
    if e1rm_kg is None and pr_metric == PRMetric.E1RM:
        raise InvalidPRCreationError(
            message="A 1RM-based PR requires e1rm_kg",
            code="e1rm_kg_required")
    
    if isinstance(exercise, int):
        exercise = Exercise.objects.get(id=exercise)

    if isinstance(source_set, int):
        source_set = Set.objects.get(id=source_set)
    
    new_pr = PR.objects.create(
        user=user,
        bodyweight_kg=bodyweight_kg,
        source_set=source_set,
        exercise=exercise,
        weight_kg=weight_kg,
        reps=reps,
        e1rm_kg=e1rm_kg,
        achieved_at=achieved_at,
        pr_metric=pr_metric,
        status=status,
        beaten_by=beaten_by,
        invalidation_reason=invalidation_reason,
        invalidated_at=invalidated_at
    )
    
    return new_pr
    

