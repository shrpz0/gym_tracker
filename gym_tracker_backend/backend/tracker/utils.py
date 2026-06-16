from datetime import datetime, timedelta
from django.utils import timezone
from datetime import datetime, date, timedelta
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta

#################################### DATES #####################################################

def start_of_day(date_obj):
    return datetime.combine(date_obj, datetime.min.time())

def start_of_next_day(date_obj):
    next_day = date_obj + timedelta(days=1)
    return datetime.combine(next_day, datetime.min.time())

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

def get_past_dt(years=0, months=0, weeks=0, days=0, hours=0):
    """
    Returns a timezone-aware datetime in the past relative to now.
    """

    if not any([years, months, weeks, days, hours]):
        raise ValueError("Provide at least one time delta")
    
    now = timezone.now()

    return now - relativedelta(
        years=years,
        months=months,
        weeks=weeks,
        days=days,
        hours=hours,
    )


def get_weeks_passed(dt):
    delta = timezone.now() - dt
    return delta.total_seconds() / (7 * 24 * 3600)


def safe_ratio(part, whole):
    return round(part / whole, 3) if whole else 0

def get_median_value(sorted_values : list):
    if not sorted_values:
        return Decimal("0.00")
    values_len = len(sorted_values)
    middle_point = values_len // 2

    if values_len % 2 != 0:
        median = sorted_values[middle_point]
        return median
    
    median = (sorted_values[middle_point - 1] + sorted_values[middle_point]) / 2
    median = round_decimal(median)
    return median


def round_decimal(value, decimal_places=2):
    quant = Decimal("1").scaleb(-decimal_places)  # e.g. 2 → Decimal("0.01")
    return value.quantize(quant, rounding=ROUND_HALF_UP)

#################################### 1RM #################################################

def get_1RM_epley(weight_kg: Decimal, reps: int):
    """Estimates 1RM according to Epleys Formula"""
    if reps == 1:
        return weight_kg
    
    return weight_kg * (Decimal(1) + Decimal(reps)/Decimal(30))

def get_1RM_brzycki(weight_kg: Decimal, reps: int):
    """Estimates 1RM according to Epleys Formula"""
    if reps == 1:
        return weight_kg

    return (weight_kg*Decimal(36))/(Decimal(37)-reps)
 
def get_1RM_avg(weight_kg, reps: int) -> Decimal:
    """Average of the two formulas"""
    if reps == 1:
        return weight_kg
    
    epley = get_1RM_epley(weight_kg, reps)
    brzycki = get_1RM_brzycki(weight_kg, reps)
    avg = (epley + brzycki) / Decimal(2)
    avg = round_decimal(avg)
    return avg


