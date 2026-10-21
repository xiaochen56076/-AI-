from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncWeek
from django.utils import timezone

from apps.activities.models import Activity, ActivityCategory
from apps.clubs.models import Club
from apps.signups.models import CheckinRecord, Signup

SUCCESS_STATUSES = [
    Signup.Status.SUCCESS,
    Signup.Status.CHECKED_IN,
    Signup.Status.NO_SHOW,
]


def _rate(numerator, denominator) -> float:
    if not denominator:
        return 0.0
    return round(numerator / denominator, 4)


def _activity_distribution(signups, field, limit=8):
    rows = (
        signups.filter(status__in=SUCCESS_STATUSES)
        .values(field)
        .annotate(value=Count("id"))
        .order_by("-value")[:limit]
    )
    distribution = []
    for row in rows:
        raw = row[field]
        if field == "user__grade" and raw is not None:
            label = f"{raw}级"
        else:
            label = raw or "未填写"
        distribution.append({"name": label, "value": row["value"]})
    return distribution


def activity_statistics(activity: Activity) -> dict:
    signups = Signup.objects.filter(activity=activity)
    counts = signups.aggregate(
        total=Count("id"),
        success=Count("id", filter=Q(status__in=SUCCESS_STATUSES)),
        waitlist=Count("id", filter=Q(status=Signup.Status.WAITLIST)),
        cancelled=Count("id", filter=Q(status=Signup.Status.CANCELLED)),
        checked_in=Count("id", filter=Q(status=Signup.Status.CHECKED_IN)),
        no_show=Count("id", filter=Q(status=Signup.Status.NO_SHOW)),
        waitlisted_ever=Count("id", filter=Q(queue_no__isnull=False)),
        promoted=Count(
            "id", filter=Q(queue_no__isnull=False, status__in=SUCCESS_STATUSES)
        ),
    )

    now = timezone.localtime()
    start_date = now.date() - timedelta(days=6)
    trend_rows = (
        signups.filter(signup_at__date__gte=start_date)
        .annotate(day=TruncDate("signup_at"))
        .values("day")
        .annotate(value=Count("id"))
    )
    trend_map = {row["day"].isoformat(): row["value"] for row in trend_rows}
    signup_trend = [
        {
            "date": (start_date + timedelta(days=offset)).isoformat(),
            "value": trend_map.get((start_date + timedelta(days=offset)).isoformat(), 0),
        }
        for offset in range(7)
    ]

    method_rows = (
        CheckinRecord.objects.filter(activity=activity)
        .values("method")
        .annotate(value=Count("id"))
        .order_by("-value")
    )
    method_labels = dict(CheckinRecord.Method.choices)
    checkin_method_distribution = [
        {"name": method_labels.get(row["method"], "其他"), "value": row["value"]}
        for row in method_rows
    ]

    return {
        "activity": {
            "id": activity.pk,
            "title": activity.title,
            "status": activity.status,
            "status_text": activity.get_status_display(),
            "capacity": activity.capacity,
            "view_count": activity.view_count,
        },
        "counts": {
            **counts,
            "signup_count": activity.signup_count,
            "waitlist_count": activity.waitlist_count,
        },
        "rates": {
            "fill_rate": _rate(counts["success"], activity.capacity),
            "checkin_rate": _rate(counts["checked_in"], counts["success"]),
            "waitlist_promotion_rate": _rate(counts["promoted"], counts["waitlisted_ever"]),
            "view_conversion_rate": _rate(counts["success"], activity.view_count),
        },
        "checkin_method_distribution": checkin_method_distribution,
        "college_distribution": _activity_distribution(signups, "user__college"),
        "grade_distribution": _activity_distribution(signups, "user__grade"),
        "signup_trend": signup_trend,
    }


def global_dashboard() -> dict:
    from apps.accounts.models import User

    now = timezone.now()
    activities = Activity.objects.filter(is_deleted=False)
    activity_counts = activities.aggregate(
        total=Count("id"),
        draft=Count("id", filter=Q(status=Activity.Status.DRAFT)),
        pending=Count("id", filter=Q(status=Activity.Status.PENDING)),
        published=Count("id", filter=Q(status=Activity.Status.PUBLISHED)),
        ended=Count("id", filter=Q(status=Activity.Status.ENDED)),
        cancelled=Count("id", filter=Q(status=Activity.Status.CANCELLED)),
        rejected=Count("id", filter=Q(status=Activity.Status.REJECTED)),
    )
    signups = Signup.objects.filter(activity__is_deleted=False)
    signup_counts = signups.aggregate(
        total=Count("id"),
        success=Count("id", filter=Q(status__in=SUCCESS_STATUSES)),
        checked_in=Count("id", filter=Q(status=Signup.Status.CHECKED_IN)),
        no_show=Count("id", filter=Q(status=Signup.Status.NO_SHOW)),
        waitlist=Count("id", filter=Q(status=Signup.Status.WAITLIST)),
    )

    category_rows = (
        activities.values("category_id", "category__name", "category__color")
        .annotate(
            activity_count=Count("id", distinct=True),
            participant_count=Count(
                "signups",
                filter=Q(signups__status__in=SUCCESS_STATUSES),
                distinct=True,
            ),
        )
        .order_by("-participant_count", "-activity_count")[:8]
    )
    popular_categories = [
        {
            "id": row["category_id"],
            "name": row["category__name"],
            "color": row["category__color"],
            "activity_count": row["activity_count"],
            "participant_count": row["participant_count"],
        }
        for row in category_rows
    ]

    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=7)
    activity_weeks = (
        activities.filter(created_at__date__gte=week_start)
        .annotate(week=TruncWeek("created_at"))
        .values("week")
        .annotate(value=Count("id"))
    )
    signup_weeks = (
        signups.filter(signup_at__date__gte=week_start)
        .annotate(week=TruncWeek("signup_at"))
        .values("week")
        .annotate(value=Count("id"))
    )

    def _week_key(value):
        return timezone.localtime(value).date().isoformat() if value else ""

    activity_map = {_week_key(row["week"]): row["value"] for row in activity_weeks}
    signup_map = {_week_key(row["week"]): row["value"] for row in signup_weeks}
    weekly_trend = []
    for offset in range(8):
        week = week_start + timedelta(weeks=offset)
        key = week.isoformat()
        weekly_trend.append(
            {
                "week": key,
                "activities": activity_map.get(key, 0),
                "signups": signup_map.get(key, 0),
            }
        )

    status_labels = dict(Activity.Status.choices)
    status_distribution = [
        {
            "status": status,
            "name": label,
            "value": activity_counts[key],
        }
        for key, status, label in [
            ("draft", Activity.Status.DRAFT, status_labels[Activity.Status.DRAFT]),
            ("pending", Activity.Status.PENDING, status_labels[Activity.Status.PENDING]),
            ("published", Activity.Status.PUBLISHED, status_labels[Activity.Status.PUBLISHED]),
            ("ended", Activity.Status.ENDED, status_labels[Activity.Status.ENDED]),
            ("cancelled", Activity.Status.CANCELLED, status_labels[Activity.Status.CANCELLED]),
            ("rejected", Activity.Status.REJECTED, status_labels[Activity.Status.REJECTED]),
        ]
    ]

    return {
        "generated_at": now.isoformat(),
        "totals": {
            "users": User.objects.filter(is_deleted=False).count(),
            "clubs": Club.objects.filter(is_deleted=False).count(),
            "categories": ActivityCategory.objects.filter(is_deleted=False).count(),
            "activities": activity_counts["total"],
            "signups": signup_counts["total"],
            "checked_in": signup_counts["checked_in"],
            "no_show": signup_counts["no_show"],
            "waitlist": signup_counts["waitlist"],
        },
        "activity_status": activity_counts,
        "signup_status": signup_counts,
        "rates": {
            "checkin_rate": _rate(signup_counts["checked_in"], signup_counts["success"]),
        },
        "status_distribution": status_distribution,
        "popular_categories": popular_categories,
        "weekly_trend": weekly_trend,
    }
