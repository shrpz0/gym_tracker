from ..models import ExerciseStrengthEvaluation, MuscleStrengthIndicator, StrengthStandard, StrengthLevel, LEVEL_TO_NUM, PR
from decimal import Decimal
from ..utils import round_decimal

# Strength evaluations are done after a new PR
# Strength evaluations happen only for select exercises -> Strength indicative exercises
# This will be used to build a user's strength profile by muscle group
# No archived evaluations, archived PRs store strength evolution history
# One exercise can only be indicative of strength for a particular muscle group for simplicity


def update_exercise_strength_evaluation(pr_instance: PR, exercise=None, user=None, bodyweight_kg=None, e1rm=None):
    if exercise is None:
        exercise = pr_instance.exercise

    if user is None:
        user = pr_instance.user

    if bodyweight_kg is None:
        bodyweight_kg = user.profile.bodyweight_kg
    
    if e1rm is None:
        e1rm = pr_instance.e1rm_kg


    lifted_multiplier = get_lifted_multiplier(bodyweight=bodyweight_kg, weight_lifted=e1rm)
    standards = get_strength_standards(exercise=exercise, sex=user.profile.sex)

    if standards is None:
        return None
    
    new_strength_level, level_threshold = get_level_and_threshold_from_standards(
        standards, 
        lifted_multiplier
    )
    
    next_level, next_level_threshold = get_level_and_threshold_closest_gt_standard(
        standards,
        lifted_multiplier
    )

    level_progress = get_level_progress(lifted_multiplier, level_threshold, next_level_threshold)
    
    existing_eval = get_existing_eval(user=user, exercise=exercise)
    if existing_eval:
        replace_old_eval(old_eval=existing_eval, 
                        new_pr=pr_instance, 
                        bodyweight_kg=bodyweight_kg,
                        new_strength_level=new_strength_level,
                        next_level=next_level,
                        level_progress=level_progress
                    )
        
        return {
            "action": "UPDATE",
            "new_strength_level": new_strength_level,
            "level_progress": level_progress,
            "next_level": next_level
        }
        
    else:
        create_new_eval(
            user=user, exercise=exercise, 
            bodyweight=bodyweight_kg, pr=pr_instance, 
            new_strength_level=new_strength_level, 
            next_level=next_level, level_progress=level_progress)

        return {
            "action": "CREATE",
            "new_strength_level": new_strength_level,
            "level_progress": level_progress,
            "next_level": next_level
        }
    

def get_strength_standards(exercise, sex):
    return StrengthStandard.objects.filter(exercise=exercise, sex=sex)


def get_lifted_multiplier(bodyweight, weight_lifted):
    return round_decimal(weight_lifted / bodyweight)

def get_level_and_threshold_from_standards(standards, lifted_multiplier):
    standard = (
        standards
        .filter(bw_multiplier__lte=lifted_multiplier)
        .order_by("-bw_multiplier")
        .first()
    )
    
    if not standard:
        return (StrengthLevel.BEGINNER, Decimal("0.00"))

    return (standard.level, standard.bw_multiplier)


def get_level_and_threshold_closest_gt_standard(standards, lifted_multiplier):
    closest_gt_standard = (
        standards
        .filter(bw_multiplier__gt=lifted_multiplier)
        .order_by("bw_multiplier")
        .first()
    )

    if not closest_gt_standard:
        return (StrengthLevel.ELITE, None)
    return (closest_gt_standard.level, closest_gt_standard.bw_multiplier)

def get_existing_eval(user, exercise):
    return (
        ExerciseStrengthEvaluation
            .objects
            .filter(user=user)
            .filter(exercise=exercise)
        ).first()


def is_new_eval_gt(old : str, new : str, old_progress : Decimal, new_progress: Decimal) -> bool :
    old_level_num = get_numeric_str_level(old)
    new_level_num = get_numeric_str_level(new)
    
    if new_level_num > old_level_num:
        return True
    
    if new_level_num == old_level_num:
        return new_progress > old_progress
    
    return False

def replace_old_eval(
        old_eval: ExerciseStrengthEvaluation, 
        bodyweight_kg: Decimal, new_pr: PR, 
        new_strength_level, next_level, 
        level_progress
    ):
    
    old_eval.pr = new_pr
    old_eval.bodyweight_kg = bodyweight_kg
    old_eval.strength_level = new_strength_level
    old_eval.evaluated_at = new_pr.achieved_at
    old_eval.level_progress = level_progress
    old_eval.next_level = next_level
    old_eval.save()


def create_new_eval(user, exercise, bodyweight, pr, new_strength_level, next_level, level_progress):
    ExerciseStrengthEvaluation.objects.create(
        user=user,
        bodyweight_kg=bodyweight,
        exercise=exercise,
        pr=pr,
        evaluated_at=pr.achieved_at,
        strength_level=new_strength_level,
        level_progress=level_progress,
        next_level=next_level
    )


def get_numeric_str_level(strength_level):
    return LEVEL_TO_NUM[strength_level]

def get_level_progress(multiplier, curr_threshold, next_threshold):
    if curr_threshold == Decimal("0.00") or next_threshold is None:
        return Decimal("0.00")

    progress = round_decimal((multiplier - curr_threshold) / (next_threshold - curr_threshold))
    return progress



