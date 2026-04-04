from ..models import Set, PR

### LOOKS UP PRS -> COMPARES THE BW/STRENGTH_STANDARD RATIO

### 

def get_strength_profile(user):

    
    qs = (
        PR
        .objects
        .filter(user=user)
        .filter()
    )

