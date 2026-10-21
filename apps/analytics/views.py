from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView

from apps.activities.repositories import get_activity_for_management
from apps.activities.services import can_admin_manage, can_manage_activity
from common.api.responses import success
from common.exceptions import BusinessError
from common.permissions import require_permission

from .services import activity_statistics, global_dashboard


class ActivityStatisticsView(APIView):
    permission_classes = [require_permission("analytics:activity")]

    @extend_schema(summary="单场活动数据看板")
    def get(self, request, pk):
        activity = get_activity_for_management(pk)
        if not activity:
            raise BusinessError("活动不存在", 30004, status.HTTP_404_NOT_FOUND)
        if not (can_manage_activity(request.user, activity) or can_admin_manage(request.user)):
            raise BusinessError(
                "只能查看自己发布活动的数据", 30002, status.HTTP_403_FORBIDDEN
            )
        return success(activity_statistics(activity), request=request)


class GlobalDashboardView(APIView):
    permission_classes = [require_permission("analytics:global")]

    @extend_schema(summary="全站数据看板")
    def get(self, request):
        return success(global_dashboard(), request=request)
