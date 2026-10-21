from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.activities.models import Activity
from apps.signups.models import Signup

from .services import notify_activity_reminders

REMINDER_HORIZON = timedelta(hours=2)


def send_activity_reminders(now=None) -> dict:
    now = now or timezone.now()
    activities = Activity.objects.filter(
        status=Activity.Status.PUBLISHED,
        is_deleted=False,
        start_time__gt=now,
        start_time__lte=now + REMINDER_HORIZON,
    )
    stats = {"activities": 0, "notifications": 0}
    for activity in activities:
        user_ids = list(
            Signup.objects.filter(
                activity=activity, status=Signup.Status.SUCCESS
            ).values_list("user_id", flat=True)
        )
        if not user_ids:
            continue
        stats["activities"] += 1
        stats["notifications"] += notify_activity_reminders(activity, user_ids)
    return stats


@shared_task
def send_activity_reminders_task():
    return send_activity_reminders()
