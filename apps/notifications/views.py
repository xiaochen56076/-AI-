from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.api.responses import paginated, success
from common.exceptions import BusinessError
from common.pagination import StandardPagination

from .models import Notification
from .repositories import query_notifications, unread_count
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="我的通知列表")
    def get(self, request):
        queryset = query_notifications(request.user, request.query_params)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginated(
            paginator,
            NotificationSerializer(page, many=True).data,
            request=request,
        )


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="未读通知数量")
    def get(self, request):
        count = unread_count(request.user)
        return success({"unread": count}, request=request)


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="标记单条通知已读")
    def post(self, request, pk):
        notification = Notification.objects.filter(pk=pk, user=request.user).first()
        if not notification:
            raise BusinessError("通知不存在", 50001, status.HTTP_404_NOT_FOUND)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        return success(
            {"id": notification.pk, "is_read": True, "unread": unread_count(request.user)},
            "已标记为已读",
            request,
        )


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="全部标记为已读")
    def post(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return success(
            {"updated": updated, "unread": 0}, f"已将 {updated} 条通知标记为已读", request
        )
