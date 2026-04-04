from ..models import PR
from django.db.models import Exists
from ..models import Set, PR, PRType

# Checks whether a PR has been achieved in this Set, if so -> Update the PR table.
# Any set with reps = 1 creates a real pr if there isn't one and updates the old real pr
# If 9 > reps > 1 then the PR is estimated and can replace other estimated PRs if the weight lifted is >
# Estimated 1RMs on sets with reps > 8 are informational only
def update_pr_new_set(set_instance: Set):
    user = set_instance.workout.user
    exercise = set_instance.exercise
    w_kg = set_instance.weight_kg
    e1rm = set_instance.estimated_1rm_kg
    dt = set_instance.workout.logged_at

    if set_instance.reps > 8:
        return {
                "pr_updated" : False
            }

    if set_instance.reps == 1:
        real_pr = (           
            PR
                .objects
                .filter(user=user)
                .filter(exercise=exercise)
                .filter(pr_type=PRType.REAL)
        ).first()

        if real_pr:
            old_value = real_pr.weight_kg
            if old_value < w_kg:
                real_pr.weight_kg = w_kg
                real_pr.achieved_at = dt
                real_pr.pr_set = set_instance
                real_pr.save()

                return {
                    "pr_updated" : True,
                    "pr_type" : "REAL",
                    "old_value" : old_value,
                    "new_value" : w_kg,
                    "exercise_name" : set_instance.exercise.name,
                    "exercise_id" : set_instance.exercise_id,
                    "set_id" : set_instance.id
                }
            
            return {
                "pr_updated" : False
            }


        else:
            PR.objects.create(
                user=user,
                exercise=exercise,
                pr_type=PRType.REAL,
                weight_kg=w_kg,
                achieved_at=dt,
                pr_set=set_instance
        )
            
            return {
                "pr_updated" : True,
                "pr_type" : "REAL",
                "old_value" : None,
                "new_value" : w_kg,
                "exercise_name" : set_instance.exercise.name,
                "exercise_id" : set_instance.exercise_id,
                "set_id" : set_instance.id

            }
        
    else:
        estimated_pr = (
            PR
                .objects
                .filter(user=user)
                .filter(exercise=exercise)
                .filter(pr_type=PRType.ESTIMATED)
        ).first()


        if estimated_pr:
            old_value = estimated_pr.weight_kg
            if old_value < e1rm:
                estimated_pr.weight_kg = e1rm
                estimated_pr.achieved_at = dt
                estimated_pr.pr_set = set_instance
                estimated_pr.save()
            
                return {
                    "pr_updated" : True,
                    "pr_type" : PRType.ESTIMATED,
                    "old_value" : old_value,
                    "new_value" : e1rm,
                    "exercise_name" : set_instance.exercise.name,
                    "exercise_id" : set_instance.exercise_id,
                    "set_id" : set_instance.id
                }
            
            return {
                "pr_updated" : False
            }

        else:
            PR.objects.create(
                user=user,
                exercise=exercise,
                pr_type=PRType.ESTIMATED,
                weight_kg=e1rm,
                achieved_at=dt,
                pr_set=set_instance
        )
            return {
                    "pr_updated" : True,
                    "pr_type" : PRType.ESTIMATED,
                    "old_value" : None,
                    "new_value" : e1rm,
                    "exercise_name" : set_instance.exercise.name,
                    "exercise_id" : set_instance.exercise_id,
                    "set_id" : set_instance.id
                }
        

### RUNS WHENEVER A SET IS DELETED, IF SET IS LINKED TO A PR, THE PR IS REPLACED BY SECOND BEST PR OF THE
# SAME TYPE IF THERE IS ONE
def handle_pr_set_deletion(pr_type : str, pr_exercise_id : int, pr_user_id : int) -> PR | None:
    if pr_type == PRType.REAL:
        new_pr_set = (
            Set
            .objects
            .filter(workout__user_id=pr_user_id)
            .filter(exercise_id=pr_exercise_id)
            .filter(reps=1)
            .order_by("-weight_kg")
        ).first()

    else:
        new_pr_set = (
            Set
            .objects
            .filter(workout__user_id=pr_user_id)
            .filter(exercise_id=pr_exercise_id)
            .filter(reps__range=(2,8))
            .order_by("-estimated_1rm_kg")
        ).first()


    if new_pr_set:
        new_pr = (
         PR
            .objects
            .create(
                user_id=pr_user_id, 
                exercise_id=pr_exercise_id,
                weight_kg=new_pr_set.estimated_1rm_kg,
                achieved_at=new_pr_set.workout.logged_at,
                pr_set=new_pr_set,
                pr_type=pr_type
            )
        
    )
        return new_pr
    
    return None
    
    


   
    


