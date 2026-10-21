from django.db.models import Q

from .models import Notification


def query_notifications(user, params):
    queryset = Notification.objects.filter(user=user).select_related("activity")
    status_value = params.get("status", "").strip()
    if status_value == "unread":
        queryset = queryset.filter(is_read=False)
    elif status_value == "read":
        queryset = queryset.filter(is_read=True)

    type_value = params.get("type", "").strip()
    if type_value.isdigit():
        queryset = queryset.filter(type=int(type_value))

    keyword = params.get("keyword", "").strip()
    if keyword:
        queryset = queryset.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))
    return queryset.order_by("-created_at", "-id")


def unread_count(user) -> int:
    return Notification.objects.filter(user=user, is_read=False).count()
