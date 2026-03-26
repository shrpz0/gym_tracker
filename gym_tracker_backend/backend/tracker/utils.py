from datetime import datetime, timedelta
from django.utils import timezone
from datetime import datetime, date, timedelta
from django.utils import timezone


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