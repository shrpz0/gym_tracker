from ..models import ExerciseStrengthEvaluation, MuscleStrengthIndicator, StrengthStandard, PRType, StrengthLevel, LEVEL_TO_NUM
from decimal import Decimal, ROUND_HALF_UP

# Strength evaluations are done after a new PR
# Strength evaluations happen only for select exercises -> Strength indicative exercises
# This will be used to build a user's strength profile by muscle group
# No archived evaluations, archived PRs store strength evolution history
# One exercise can only be indicative of strength for a particular muscle group for simplicity
# Strength evals from REAL PRs get priority and replace all evals coming from ESTIMATED PRs for accuracy
# 

def update_exercise_strength_evaluation_from_pr(pr_instance):
    exercise = pr_instance.exercise
    user = pr_instance.user
    new_pr_type = pr_instance.pr_type

    existing_eval = (
        ExerciseStrengthEvaluation
        .objects
        .filter(user=user)
        .filter(exercise=exercise)
        .first()
    )


    if existing_eval:
        if new_pr_type == existing_eval.source_pr_type:
            standards = get_strength_standards(exercise, user.profile.sex)
            new_strength_level = get_strength_level_from_standards(standards, 
                                                               user.profile.bodyweight_kg, 
                                                               pr_instance.weight_kg)
            
            if is_new_level_gt(existing_eval.strength_level, new_strength_level):
                replace_old_eval(existing_eval, pr_instance, new_pr_type, new_strength_level)

                return {
                    "strength_eval_updated" : True,
                    "new_strength_level" : new_strength_level
                }
            


        elif new_pr_type == PRType.ESTIMATED:
            return {
                "strength_eval_updated" : False,
            }
        
        else:
            standards = get_strength_standards(exercise, user.profile.sex)
            new_strength_level = get_strength_level_from_standards(standards, 
                                                               user.profile.bodyweight_kg, 
                                                               pr_instance.weight_kg)
            
            replace_old_eval(existing_eval, pr_instance, new_pr_type, new_strength_level)
            return {
                "strength_eval_updated": True,
                "new_strength_level": new_strength_level
            }

    
    else:
        standards = get_strength_standards(exercise, user.profile.sex)
        new_strength_level = get_strength_level_from_standards(standards, 
                                                               user.profile.bodyweight_kg, 
                                                               pr_instance.weight_kg)
        create_new_eval(user, exercise, pr_instance, new_pr_type, new_strength_level)
        return {
            "strength_eval_updated": True,
            "new_strength_level": new_strength_level
        }



def get_strength_standards(exercise, sex):
    return StrengthStandard.objects.filter(exercise=exercise, sex=sex)

def get_strength_level_from_standards(standards, bodyweight, weight_lifted):
    lifted_multiplier = (weight_lifted / bodyweight).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    standard = (
        standards
        .filter(bw_multiplier__lte=lifted_multiplier)
        .order_by("-bw_multiplier")
        .first()
    )
    
    return standard.level if standard else StrengthLevel.BEGINNER

def is_new_level_gt(old : str, new : str) -> bool :
    old_level_num = get_numeric_str_level(old)
    new_level_num = get_numeric_str_level(new)

    return new_level_num > old_level_num

def replace_old_eval(old_eval, new_pr, new_pr_type, new_strength_level):
    old_eval.pr = new_pr
    old_eval.source_pr_type = new_pr_type
    old_eval.strength_level = new_strength_level
    old_eval.evaluated_at = new_pr.achieved_at
    old_eval.save()
    
def create_new_eval(user, exercise, pr, pr_type, new_strength_level):
    ExerciseStrengthEvaluation.objects.create(
        user=user,
        exercise=exercise,
        pr=pr,
        source_pr_type=pr_type,
        evaluated_at=pr.achieved_at,
        strength_level=new_strength_level
    )


def get_numeric_str_level(strength_level):
    return LEVEL_TO_NUM[strength_level]

