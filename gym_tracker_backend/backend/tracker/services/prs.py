from ..models import PR
from django.db.models import Exists
from django.utils import timezone
### Checks whether a PR has been achieved in this Set, if so -> Update the PR table.
### Any set with reps = 1 creates a real pr if there isn't one and updates (if new weight is >) the old real pr
### If reps > 1 then the PR is estimated and can replace other estimated PRs if the weight lifted is >
def update_pr_for_set(set_instance):
    user = set_instance.workout.user
    exercise = set_instance.exercise
    rm = set_instance.estimated_1rm_kg

    if set_instance.reps == 1:
        real_pr = (           
            PR
                .objects
                .filter(user=user)
                .filter(exercise=exercise)
                .filter(pr_type="ACTUAL")
        ).first()

        if real_pr:
            if real_pr.weight_kg < rm:
                real_pr.weight_kg = set_instance.weight_kg
                real_pr.achieved_at = timezone.now()
                real_pr.save()

        else:
            PR.objects.create(
                user=user,
                exercise=exercise,
                pr_type="ACTUAL",
                weight_kg=set_instance.weight_kg,
                achieved_at=timezone.now()
        )
        
    else:
        estimated_pr = (
            PR
                .objects
                .filter(user=user)
                .filter(exercise=exercise)
                .filter(pr_type="ESTIMATED")
        ).first()


        if estimated_pr:
            if estimated_pr.weight_kg < rm:
                estimated_pr.weight_kg = rm
                estimated_pr.achieved_at = timezone.now()
                estimated_pr.save()

        else:
            PR.objects.create(
                user=user,
                exercise=exercise,
                type_pr="ESTIMATED",
                weight_kg=rm,
                achieved_at=timezone.now()
        )



    
    

   
    


