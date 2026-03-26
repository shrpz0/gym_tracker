from datetime import datetime, timedelta
from django.utils import timezone
from datetime import datetime, date, timedelta
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP


def get_week_range(given_date: date):
    start_date = given_date - timedelta(days=given_date.weekday())
    end_date = start_date + timedelta(days=7)

    tz = timezone.get_current_timezone()

    start_dt = timezone.make_aware(
        datetime.combine(start_date, datetime.min.time()),
        tz
    )
    end_dt = timezone.make_aware(
        datetime.combine(end_date, datetime.min.time()),
        tz
    )

    return start_dt, end_dt

def get_month_range(given_date: date):
    start_date = given_date.replace(day=1)

    if given_date.month == 12:
        next_month = given_date.replace(year=given_date.year + 1, month=1, day=1)
    else:
        next_month = given_date.replace(month=given_date.month+1, day=1)

    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(
        datetime.combine(start_date, datetime.min.time()),
        tz

    )

    end_dt = timezone.make_aware(
        datetime.combine(next_month, datetime.min.time()),
        tz
    )

    return start_dt, end_dt


def safe_ratio(part, whole):
    return round(part / whole, 3) if whole else 0

### Estimates 1RM according to Epleys Formula
def get_1RM_epley(weight_kg: Decimal, reps: int):
    return weight_kg * (Decimal(1) + Decimal(reps)/Decimal(30))

### Estimates 1RM according to Epleys Formula
def get_1RM_brzycki(weight_kg: Decimal, reps: int):
    return (weight_kg*Decimal(36))/(Decimal(37)-reps)

### Average of the two formulas
def get_1RM_avg(weight_kg, reps: int) -> Decimal:
    epley = get_1RM_epley(weight_kg, reps)
    brzycki = get_1RM_brzycki(weight_kg, reps)
    avg = (epley + brzycki) / Decimal(2)

    return avg.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)