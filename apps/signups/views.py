import csv

from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.activities.repositories import get_activity_for_management
from common.api.responses import paginated, success
from common.exceptions import BusinessError
from common.pagination import StandardPagination

from .repositories import query_activity_signups, query_my_signups
from .serializers import MySignupSerializer, SignupSerializer, serialize_signup_result
from .services import (
    build_csv_rows,
    cancel_signup,
    ensure_can_manage_roster,
    signup_for_activity,
)
from .throttles import SignupRateThrottle


class ActivitySignupView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [SignupRateThrottle]

    @extend_schema(summary="报名活动（满员自动进入候补）")
    def post(self, request, pk):
        signup, created = signup_for_activity(pk, request.user, request.data.get("remark", ""))
        message = "报名成功" if signup.status == 1 else "名额已满，已进入候补队列"
        if not created:
            message = "你已报名过该活动"
        return success(serialize_signup_result(signup, request), message, request)

    @extend_schema(summary="取消报名")
    def delete(self, request, pk):
        signup, promoted = cancel_signup(pk, request.user)
        data = {
            "signup_id": signup.pk,
            "status": signup.status,
            "status_text": signup.status_text,
            "promoted_signup_id": promoted.pk if promoted else None,
        }
        return success(data, "已取消报名", request)


class MySignupsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="我的活动/我的报名")
    def get(self, request):
        queryset = query_my_signups(request.user, request.query_params)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginated(
            paginator,
            MySignupSerializer(page, many=True, context={"request": request}).data,
            request=request,
        )


def _get_owned_activity(request, pk):
    activity = get_activity_for_management(pk)
    if not activity:
        raise BusinessError("活动不存在", 30004, status.HTTP_404_NOT_FOUND)
    ensure_can_manage_roster(request.user, activity)
    return activity


class ActivitySignupListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="主办方查看报名名单")
    def get(self, request, pk):
        activity = _get_owned_activity(request, pk)
        queryset = query_activity_signups(activity, request.query_params)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginated(
            paginator,
            SignupSerializer(page, many=True, context={"request": request}).data,
            request=request,
        )


def _safe_csv_cell(value):
    text = str(value or "")
    if text.startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text


class ActivitySignupExportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="导出报名名单 CSV")
    def get(self, request, pk):
        activity = _get_owned_activity(request, pk)
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        filename = f"activity-{activity.pk}-signups.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(["学号", "姓名", "学院", "报名状态", "候补序号", "报名时间"])
        for row in build_csv_rows(activity):
            writer.writerow([_safe_csv_cell(cell) for cell in row])
        return response
