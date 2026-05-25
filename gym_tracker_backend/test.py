from decimal import Decimal

def get_1RM_epley(weight_kg: Decimal, reps: int):
    """Estimates 1RM according to Epleys Formula"""

    return weight_kg * (Decimal(1) + Decimal(reps)/Decimal(30))

def get_1RM_brzycki(weight_kg: Decimal, reps: int):
    """Estimates 1RM according to Epleys Formula"""

    return (weight_kg*Decimal(36))/(Decimal(37)-reps)
 
def get_1RM_avg(weight_kg, reps: int) -> Decimal:
    """Average of the two formulas"""

    epley = get_1RM_epley(weight_kg, reps)
    brzycki = get_1RM_brzycki(weight_kg, reps)
    avg = (epley + brzycki) / Decimal(2)

    return avg

#################################### PR ####################################
def get_rep_multiplier(reps: int) -> Decimal:
    return min(1, Decimal(0.85**((reps-3) / 9)))
    

def get_PR_score(e1rm: Decimal, reps: int):
    return get_rep_multiplier(reps) * e1rm
    



w = 0.1
while w <= 500:
    values = []
    for r in range(1, 13):
        e1rm = get_1RM_avg(weight_kg=Decimal(w), reps=r)
        score = get_PR_score(e1rm, r)

        if values and max(values) > score:
            raise ValueError(f"BROKEN SHIT, {values} | {score} | {r}")

        values.append(score)

    w += 0.1

print("reps monotonicity OK")

for r in range(1, 13):
    last = None
    w = 0.1
    while w <= 250:
        e1rm = get_1RM_avg(Decimal(w), r)
        score = get_PR_score(e1rm, r)

        if last is not None and score < last:
            raise ValueError(f"Weight monotonicity broken at reps={r}, w={w}")

        last = score
        w += 0.1

print("weight monotonicity OK")


def test_cross_rep_fairness():
    for w1 in [Decimal(x) for x in range(5, 201)]:
        for r1 in range(1, 7):  # low reps
            e1rm1 = get_1RM_avg(w1, r1)
            score1 = get_PR_score(e1rm1, r1)

            for w2 in [Decimal(x) for x in range(1, int(w1))]:
                for r2 in range(7, 13):  # high reps
                    e1rm2 = get_1RM_avg(w2, r2)
                    score2 = get_PR_score(e1rm2, r2)

                    # If low-rep e1RM is >= high-rep e1RM, low-rep MUST win
                    if e1rm1 >= e1rm2 and score2 > score1:
                        raise ValueError(
                            f"Cross-rep fairness broken:\n"
                            f"Low-rep {w1}x{r1} (e1rm={e1rm1}, score={score1}) < "
                            f"High-rep {w2}x{r2} (e1rm={e1rm2}, score={score2})"
                        )

                    # If e1rm2 is only slightly higher (<1%), low-rep should still win
                    if e1rm2 < e1rm1 * Decimal("1.01") and score2 > score1:
                        raise ValueError(
                            f"Near-equal e1RM fairness broken:\n"
                            f"{w1}x{r1} vs {w2}x{r2}"
                        )

    print("Cross-rep fairness: OK")




def test_rep_smoothness():
    for w in [Decimal(x) for x in range(5, 201)]:
        scores = []
        for r in range(1, 13):
            e1rm = get_1RM_avg(w, r)
            score = get_PR_score(e1rm, r)
            scores.append(score)

        # Strict monotonicity
        for i in range(1, len(scores)):
            if scores[i] < scores[i-1]:
                raise ValueError(
                    f"Rep monotonicity broken at weight={w}, reps={i+1}: "
                    f"{scores[i]} < {scores[i-1]}"
                )

        # Strict curvature: no dips or spikes
        for i in range(1, len(scores)-1):
            left = scores[i-1]
            mid = scores[i]
            right = scores[i+1]

            # Midpoint should not be far below average of neighbors
            if mid < (left + right) / 2 - Decimal("0.25"):
                raise ValueError(
                    f"Rep smoothness broken at weight={w}, reps={i+1}: "
                    f"dip detected {left}, {mid}, {right}"
                )

    print("Rep smoothness: OK")

def test_weight_smoothness():
    for r in range(1, 13):
        last_score = None
        for w in [Decimal(x) / Decimal(10) for x in range(1, 2000)]:  # 0.1 → 200.0
            e1rm = get_1RM_avg(w, r)
            score = get_PR_score(e1rm, r)

            if last_score is not None:
                # Must be monotonic
                if score < last_score:
                    raise ValueError(
                        f"Weight monotonicity broken at reps={r}, weight={w}: "
                        f"{score} < {last_score}"
                    )

                # Must be smooth (no sudden jumps)
                if score - last_score > Decimal("2.0"):
                    raise ValueError(
                        f"Weight smoothness broken at reps={r}, weight={w}: "
                        f"jump {last_score} → {score}"
                    )

            last_score = score

    print("Weight smoothness: OK")

        
test_cross_rep_fairness()
test_weight_smoothness()
test_rep_smoothness()


def test_higher_rep_higher_e1rm_wins():
    weights = [Decimal(x) / Decimal(2) for x in range(2, 500)]  # 1.0 → 250.0

    for wA in weights:
        for rA in range(1, 13):
            e1A = get_1RM_avg(wA, rA)
            prA = get_PR_score(e1A, rA)

            for wB in weights:
                for rB in range(1, 13):

                    # Only test cases where A should win
                    if rA > rB:
                        e1B = get_1RM_avg(wB, rB)
                        prB = get_PR_score(e1B, rB)

                        # A has equal or higher e1RM
                        if e1A >= e1B:
                            # A MUST win
                            if prA - prB > - 0.1:
                                raise ValueError(
                                    f"FAIL: Higher-rep higher-e1RM set lost\n"
                                    f"A: {wA} x {rA} (e1rm={e1A}, pr={prA})\n"
                                    f"B: {wB} x {rB} (e1rm={e1B}, pr={prB})"
                                )

    print("Higher-rep + higher-e1RM dominance OK")

test_higher_rep_higher_e1rm_wins()
