from datetime import datetime, timedelta
from django.utils import timezone

def parse_date_range(start_date: str, end_date: str):
    """
    Converts:
        start_date: "YYYY-MM-DD"
        end_date: "YYYY-MM-DD"
    Into:
        start_dt = start_date at 00:00:00
        end_dt   = next day at 00:00:00
    Returns timezone-aware datetimes.
    """

    if not start_date or not end_date:
        raise ValueError("Both start_date and end_date are required")

    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Dates must be in YYYY-MM-DD format")

    end_dt = end_dt + timedelta(days=1)

    start_dt = timezone.make_aware(start_dt)
    end_dt = timezone.make_aware(end_dt)

    return start_dt, end_dt

def safe_ratio(part, whole):
    return round(part / whole, 3) if whole else 0