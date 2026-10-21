from django.db.models import F
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from common.api.responses import created, paginated, success
from common.exceptions import BusinessError
from common.pagination import StandardPagination
from common.permissions import require_permission

from .models import Activity, ActivityCategory, ActivityTag
from .repositories import (
    get_activity_for_management,
    get_activity_for_view,
    query_favorites,
    query_my_activities,
    query_pending_audits,
    query_public_activities,
)
from .serializers import (
    ActivityBriefSerializer,
    ActivityDetailSerializer,
    ActivityWriteSerializer,
    AuditActionSerializer,
    CancelActivitySerializer,
    CategorySerializer,
    TagSerializer,
)
from .services import (
    add_favorite,
    cancel_activity,
    create_activity,
    remove_favorite,
    review_activity,
    submit_activity,
    update_activity,
    user_can_view_activity,
)


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="活动分类列表")
    def get(self, request):
        categories = ActivityCategory.objects.filter(is_active=True, is_deleted=False)
        return success(CategorySerializer(categories, many=True).data, request=request)


class TagListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="活动标签列表")
    def get(self, request):
        tags = ActivityTag.objects.filter(is_active=True, is_deleted=False)
        return success(TagSerializer(tags, many=True).data, request=request)


class ActivityListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [require_permission("activity:create")()]

    @extend_schema(summary="活动列表（检索/筛选/分页）")
    def get(self, request):
        queryset = query_public_activities(user=request.user, params=request.query_params)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginated(
            paginator,
            ActivityBriefSerializer(page, many=True, context={"request": request}).data,
            request=request,
        )

    @extend_schema(summary="主办方创建活动草稿")
    def post(self, request):
        serializer = ActivityWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activity = create_activity(request.user, dict(serializer.validated_data))
        detail = get_activity_for_view(activity.pk, request.user)
        return created(
            ActivityDetailSerializer(detail, context={"request": request}).data,
            "活动草稿已创建",
            request,
        )


class ActivityDetailView(APIView):
    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAuthenticated()]

    def get_object(self, request, pk):
        activity = get_activity_for_view(pk, request.user)
        if not activity or not user_can_view_activity(request.user, activity):
            raise BusinessError("活动不存在或尚未公开", 30004, status.HTTP_404_NOT_FOUND)
        return activity

    @extend_schema(summary="活动详情")
    def get(self, request, pk):
        activity = self.get_object(request, pk)
        if activity.status in {Activity.Status.PUBLISHED, Activity.Status.ENDED}:
            Activity.objects.filter(pk=activity.pk).update(view_count=F("view_count") + 1)
            activity.view_count += 1
        return success(
            ActivityDetailSerializer(activity, context={"request": request}).data,
            request=request,
        )

    @extend_schema(summary="编辑活动")
    def patch(self, request, pk):
        existing = get_activity_for_management(pk)
        if not existing:
            raise BusinessError("活动不存在", 30004, status.HTTP_404_NOT_FOUND)
        serializer = ActivityWriteSerializer(existing, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        activity = update_activity(pk, request.user, dict(serializer.validated_data))
        refreshed = get_activity_for_view(activity.pk, request.user)
        return success(
            ActivityDetailSerializer(refreshed, context={"request": request}).data,
            "活动信息已更新",
            request,
        )


class ActivitySubmitView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="提交活动审核")
    def post(self, request, pk):
        activity = submit_activity(pk, request.user)
        refreshed = get_activity_for_view(activity.pk, request.user)
        return success(
            ActivityDetailSerializer(refreshed, context={"request": request}).data,
            "已提交审核，请等待审核结果",
            request,
        )


class ActivityCancelView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="取消/下架活动")
    def post(self, request, pk):
        serializer = CancelActivitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activity = cancel_activity(pk, request.user, serializer.validated_data["reason"])
        refreshed = get_activity_for_view(activity.pk, request.user)
        return success(
            ActivityDetailSerializer(refreshed, context={"request": request}).data,
            "活动已取消",
            request,
        )


class ActivityFavoriteView(APIView):
    permission_classes = [IsAuthenticated]

    def get_activity(self, pk):
        activity = get_activity_for_view(pk)
        if not activity:
            raise BusinessError("活动不存在", 30004, status.HTTP_404_NOT_FOUND)
        return activity

    @extend_schema(summary="收藏活动")
    def post(self, request, pk):
        created_flag = add_favorite(request.user, self.get_activity(pk))
        return success(
            {"is_favorited": True}, "已加入收藏" if created_flag else "已收藏过该活动", request
        )

    @extend_schema(summary="取消收藏")
    def delete(self, request, pk):
        remove_favorite(request.user, self.get_activity(pk))
        return success({"is_favorited": False}, "已取消收藏", request)


class MyActivitiesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="我发布的活动（主办方）")
    def get(self, request):
        queryset = query_my_activities(request.user, request.query_params)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginated(
            paginator,
            ActivityBriefSerializer(page, many=True, context={"request": request}).data,
            request=request,
        )


class MyFavoritesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="我的收藏")
    def get(self, request):
        queryset = query_favorites(request.user)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginated(
            paginator,
            ActivityBriefSerializer(page, many=True, context={"request": request}).data,
            request=request,
        )


class AdminAuditListView(APIView):
    permission_classes = [require_permission("activity:audit")]

    @extend_schema(summary="审核工作台列表")
    def get(self, request):
        queryset = query_pending_audits(request.query_params)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        data = ActivityDetailSerializer(page, many=True, context={"request": request}).data
        return paginated(paginator, data, request=request)


class AdminAuditActionView(APIView):
    permission_classes = [require_permission("activity:audit")]

    @extend_schema(summary="通过或驳回活动")
    def post(self, request, pk):
        serializer = AuditActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activity = review_activity(
            pk,
            request.user,
            serializer.validated_data["action"],
            serializer.validated_data["comment"],
        )
        refreshed = get_activity_for_view(activity.pk, request.user)
        message = (
            "活动已通过审核并发布" if serializer.validated_data["action"] == 1 else "活动已驳回"
        )
        return success(
            ActivityDetailSerializer(refreshed, context={"request": request}).data,
            message,
            request,
        )
