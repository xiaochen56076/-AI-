from django.db.models import Q
from django.utils import timezone

from .models import Signup


def query_my_signups(user, params):
    queryset = (
        Signup.objects.filter(user=user, activity__is_deleted=False)
        .select_related(
            "activity",
            "activity__category",
            "activity__club",
            "activity__organizer",
            "checkin_record",
        )
        .prefetch_related("activity__tags")
    )
    group = params.get("group", "").strip()
    now = timezone.now()
    if group == "waitlist":
        queryset = queryset.filter(status=Signup.Status.WAITLIST)
    elif group == "upcoming":
        queryset = queryset.filter(status=Signup.Status.SUCCESS, activity__end_time__gte=now)
    elif group == "attended":
        queryset = queryset.filter(status__in=[Signup.Status.CHECKED_IN, Signup.Status.NO_SHOW])
    elif group == "cancelled":
        queryset = queryset.filter(status=Signup.Status.CANCELLED)
    return queryset.order_by("-signup_at")


def query_activity_signups(activity, params):
    queryset = Signup.objects.filter(activity=activity).select_related("user", "checkin_record")
    status_value = params.get("status", "").strip()
    if status_value.isdigit():
        queryset = queryset.filter(status=int(status_value))
    keyword = params.get("keyword", "").strip()
    if keyword:
        queryset = queryset.filter(
            Q(user__student_no__icontains=keyword)
            | Q(user__real_name__icontains=keyword)
            | Q(user__nickname__icontains=keyword)
        )
    return queryset.order_by("status", "queue_no", "signup_at")
