from decimal import Decimal, ROUND_HALF_UP

def round_decimal(value, decimal_places=2):
    quant = Decimal("1").scaleb(-decimal_places)  # e.g. 2 → Decimal("0.01")
    return value.quantize(quant, rounding=ROUND_HALF_UP)

def get_1RM_epley(weight_kg: Decimal, reps: int):
    """Estimates 1RM according to Epleys Formula"""

    return weight_kg * (Decimal(1) + Decimal(reps)/Decimal(30))

def get_1RM_brzycki(weight_kg: Decimal, reps: int):
    """Estimates 1RM according to Epleys Formula"""

    return (weight_kg*Decimal(36))/(Decimal(37)-reps)
 
def get_1RM_avg(weight_kg, reps: int) -> Decimal:
    """Average of the two formulas"""

    if reps == 1:
        return [weight_kg, f"Weight = {weight_kg} ||| Reps = {reps} ||| ESTIMATED 1RM = {weight_kg}"]

    
    epley = get_1RM_epley(weight_kg, reps)
    brzycki = get_1RM_brzycki(weight_kg, reps)
    avg = (epley + brzycki) / Decimal(2)
    avg = round_decimal(avg)
    return [avg, f"Weight = {weight_kg} ||| Reps = {reps} ||| ESTIMATED 1RM = {avg}"]

def get_lifted_multiplier(bodyweight, weight_lifted):
    return f"Lifted Multiplier = {round_decimal(weight_lifted / bodyweight)}"

print(f"{'-'*100}")
bw = Decimal(input("Bodyweight = "))
w = Decimal(input("Weight = "))
r = int(input("reps = "))

rm, output = get_1RM_avg(w, r)
print(output)
print(get_lifted_multiplier(bodyweight=bw, weight_lifted=rm))
print(f"{'-'*100}")

