from ..models import PR
from django.db.models import Exists
from django.utils import timezone
### Checks whether a PR has been achieved in this Set, if so -> Update the PR table.
### Any set with reps = 1 creates a real pr if there isn't one and updates (if new weight is >) the old real pr
### If reps > 1 then the PR is estimated and can replace other estimated PRs if the weight lifted is >
def update_pr_for_set(set_instance):
    user = set_instance.workout.user
    exercise = set_instance.exercise
    w_kg = set_instance.weight_kg
    e1rm = set_instance.estimated_1rm_kg
    dt = set_instance.workout.logged_at

    if set_instance.reps == 1:
        real_pr = (           
            PR
                .objects
                .filter(user=user)
                .filter(exercise=exercise)
                .filter(pr_type="ACTUAL")
        ).first()

        if real_pr:
            if real_pr.weight_kg < w_kg:
                real_pr.weight_kg = w_kg
                real_pr.achieved_at = dt
                real_pr.save()

                return {
                    "pr_updated" : True,
                    "pr_type" : "REAL",
                    "old_value" : real_pr.weight_kg,
                    "new_value" : w_kg,
                    "exercise_name" : set_instance.exercise.name,
                    "exercise_id" : set_instance.exercise_id
                }
            
            return {
                "pr_updated" : False
            }


        else:
            PR.objects.create(
                user=user,
                exercise=exercise,
                pr_type="ACTUAL",
                weight_kg=w_kg,
                achieved_at=dt
        )
            
            return {
                "pr_updated" : True,
                "pr_type" : "REAL",
                "old_value" : None,
                "new_value" : w_kg,
                "exercise_name" : set_instance.exercise.name,
                "exercise_id" : set_instance.exercise_id
                }
        
    else:
        estimated_pr = (
            PR
                .objects
                .filter(user=user)
                .filter(exercise=exercise)
                .filter(pr_type="ESTIMATED")
        ).first()


        if estimated_pr:
            if estimated_pr.weight_kg < e1rm:
                estimated_pr.weight_kg = e1rm
                estimated_pr.achieved_at = dt
                estimated_pr.save()
            
                return {
                    "pr_updated" : True,
                    "pr_type" : "ESTIMATED",
                    "old_value" : estimated_pr.weight_kg,
                    "new_value" : e1rm,
                    "exercise_name" : set_instance.exercise.name,
                    "exercise_id" : set_instance.exercise_id
                }
            
            return {
                "pr_updated" : False
            }

        else:
            PR.objects.create(
                user=user,
                exercise=exercise,
                pr_type="ESTIMATED",
                weight_kg=e1rm,
                achieved_at=dt
        )
            return {
                    "pr_updated" : True,
                    "pr_type" : "ESTIMATED",
                    "old_value" : None,
                    "new_value" : e1rm,
                    "exercise_name" : set_instance.exercise.name,
                    "exercise_id" : set_instance.exercise_id
                }



    
    

   
    


