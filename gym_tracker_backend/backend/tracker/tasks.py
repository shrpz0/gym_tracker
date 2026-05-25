from .services.prs import invalidate_expired_prs
from celery import shared_task
from django.conf import settings

@shared_task(bind=True, max_retries=3)
def expire_prs_task(self):
    total_stats = {
        "candidates": 0,
        "expired_no_replacement": 0,
        "expired_replaced": 0,
        "skipped": 0,
        "race_conflicts": 0,
        "errors": 0,
        "batches": 0,
    }

    batch_size = getattr(settings, "PR_EXPIRATION_BATCH_SIZE", 500)

    while True:
        stats = invalidate_expired_prs(batch_size=batch_size)
        total_stats["batches"] += 1

        for key, value in stats.items():
            total_stats[key] = total_stats.get(key, 0) + value

        if stats.get("candidates", 0) == 0:
            break

    return total_stats
    
