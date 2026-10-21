from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.signups.models import Signup

from .models import Activity


def close_expired_activities(now=None) -> dict:
    now = now or timezone.now()
    activity_ids = list(
        Activity.objects.filter(
            status=Activity.Status.PUBLISHED,
            end_time__lt=now,
            is_deleted=False,
        ).values_list("pk", flat=True)
    )
    stats = {"activities": 0, "no_shows": 0, "waitlist_cancelled": 0}

    for activity_id in activity_ids:
        with transaction.atomic():
            activity = (
                Activity.objects.select_for_update()
                .filter(pk=activity_id, is_deleted=False)
                .first()
            )
            if (
                not activity
                or activity.status != Activity.Status.PUBLISHED
                or activity.end_time >= now
            ):
                continue
            activity.status = Activity.Status.ENDED
            activity.save(update_fields=["status", "updated_at"])

            signups = Signup.objects.filter(activity=activity)
            if activity.checkin_mode != Activity.CheckinMode.NONE:
                stats["no_shows"] += signups.filter(status=Signup.Status.SUCCESS).update(
                    status=Signup.Status.NO_SHOW, updated_at=now
                )
            stats["waitlist_cancelled"] += signups.filter(
                status=Signup.Status.WAITLIST
            ).update(status=Signup.Status.CANCELLED, cancel_at=now, updated_at=now)
            Activity.objects.filter(pk=activity.pk).update(waitlist_count=0)
            stats["activities"] += 1

    return stats


@shared_task
def close_expired_activities_task():
    return close_expired_activities()
