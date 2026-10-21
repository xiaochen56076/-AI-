from django.db.models import BooleanField, Exists, OuterRef, Q, Value
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import Activity, Favorite


def annotate_favorite(queryset, user):
    if user and user.is_authenticated:
        favorites = Favorite.objects.filter(activity_id=OuterRef("pk"), user_id=user.id)
        return queryset.annotate(is_favorited_flag=Exists(favorites))
    return queryset.annotate(is_favorited_flag=Value(False, output_field=BooleanField()))


def base_activity_queryset(user=None):
    queryset = (
        Activity.objects.filter(is_deleted=False)
        .select_related("category", "club", "organizer")
        .prefetch_related("tags", "audit_records")
    )
    return annotate_favorite(queryset, user)


def public_activity_queryset(user=None):
    return base_activity_queryset(user).filter(
        status__in=[Activity.Status.PUBLISHED, Activity.Status.ENDED]
    )


def query_public_activities(*, user=None, params):
    queryset = public_activity_queryset(user)
    now = timezone.now()

    scope = params.get("scope", "upcoming")
    if scope == "upcoming":
        queryset = queryset.filter(Q(status=Activity.Status.PUBLISHED, end_time__gte=now))
    elif scope == "past":
        queryset = queryset.filter(
            Q(status=Activity.Status.ENDED) | Q(status=Activity.Status.PUBLISHED, end_time__lt=now)
        )

    keyword = params.get("keyword", "").strip()
    if keyword:
        queryset = queryset.filter(
            Q(title__icontains=keyword)
            | Q(summary__icontains=keyword)
            | Q(location__icontains=keyword)
            | Q(club__name__icontains=keyword)
        )

    category = params.get("category", "").strip()
    if category:
        queryset = queryset.filter(category__slug=category)

    tag = params.get("tag", "").strip()
    if tag:
        queryset = (
            queryset.filter(tags__id=tag) if tag.isdigit() else queryset.filter(tags__name=tag)
        )

    date_from = parse_date(params.get("date_from", ""))
    date_to = parse_date(params.get("date_to", ""))
    if date_from:
        queryset = queryset.filter(start_time__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(start_time__date__lte=date_to)

    sort = params.get("sort", "start_time")
    ordering = {
        "start_time": ("start_time", "id"),
        "latest": ("-created_at",),
        "hot": ("-view_count", "-signup_count"),
        "deadline": ("signup_end",),
    }.get(sort, ("start_time", "id"))
    return queryset.order_by(*ordering).distinct()


def get_activity_for_view(pk, user=None):
    return base_activity_queryset(user).filter(pk=pk).first()


def get_activity_for_management(pk):
    return (
        Activity.objects.filter(pk=pk, is_deleted=False)
        .select_related("category", "club", "organizer")
        .prefetch_related("tags")
        .first()
    )


def query_my_activities(user, params):
    queryset = base_activity_queryset(user).filter(organizer=user)
    status_value = params.get("status", "").strip()
    if status_value.isdigit():
        queryset = queryset.filter(status=int(status_value))
    keyword = params.get("keyword", "").strip()
    if keyword:
        queryset = queryset.filter(Q(title__icontains=keyword) | Q(location__icontains=keyword))
    return queryset.order_by("-updated_at")


def query_favorites(user):
    return (
        base_activity_queryset(user)
        .filter(favorited_by__user=user)
        .order_by("-favorited_by__created_at")
    )


def query_pending_audits(params):
    queryset = (
        Activity.objects.filter(is_deleted=False)
        .select_related("category", "club", "organizer")
        .prefetch_related("tags")
    )
    status_value = params.get("status", str(Activity.Status.PENDING)).strip()
    if status_value.isdigit():
        queryset = queryset.filter(status=int(status_value))
    keyword = params.get("keyword", "").strip()
    if keyword:
        queryset = queryset.filter(
            Q(title__icontains=keyword) | Q(organizer__real_name__icontains=keyword)
        )
    return queryset.order_by("updated_at", "id")
