from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenViewBase

from common.api.responses import paginated, success
from common.exceptions import BusinessError
from common.pagination import StandardPagination
from common.permissions import require_permission

from .authentication import access_blacklist_key
from .models import Role, User
from .serializers import (
    AdminUserUpdateSerializer,
    CampusTokenObtainSerializer,
    ChangePasswordSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    RoleBriefSerializer,
    UserSerializer,
)
from .services import issue_tokens, register_student, update_user_by_admin


class RegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(summary="学生注册")
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = register_student(serializer.validated_data)
        data = issue_tokens(user, request)
        return success(
            data, "注册成功，欢迎加入 CampusHub", request, status=status.HTTP_201_CREATED
        )


class LoginView(TokenViewBase):
    permission_classes = [AllowAny]
    serializer_class = CampusTokenObtainSerializer

    @extend_schema(summary="学号密码登录")
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        data = dict(serializer.validated_data)
        data["expires_in"] = 7200
        data["user"] = UserSerializer(user, context={"request": request}).data
        return success(data, "登录成功", request)


class RefreshView(APIView):
    permission_classes = [AllowAny]
    serializer_class = TokenRefreshSerializer

    @extend_schema(summary="刷新访问令牌")
    def post(self, request, *args, **kwargs):
        serializer = TokenRefreshSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise AuthenticationFailed("刷新令牌无效或已过期") from exc
        data = dict(serializer.validated_data)
        if "refresh" in data:
            data["expires_in"] = 7200
        return success(data, "令牌已刷新", request)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="退出登录")
    def post(self, request):
        refresh_value = request.data.get("refresh")
        if refresh_value:
            try:
                RefreshToken(refresh_value).blacklist()
            except TokenError:
                pass
        access = request.auth
        if access is not None:
            remaining = int(access.get("exp", 0)) - int(__import__("time").time())
            if remaining > 0:
                cache.set(access_blacklist_key(access["jti"]), True, timeout=remaining)
        return success(None, "已安全退出", request)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="获取当前用户")
    def get(self, request):
        return success(
            UserSerializer(request.user, context={"request": request}).data, request=request
        )

    @extend_schema(summary="更新个人资料")
    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success(
            UserSerializer(request.user, context={"request": request}).data,
            "个人资料已更新",
            request,
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="修改密码")
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password", "updated_at"])
        return success(None, "密码已修改，请重新登录", request)


class AdminUserListView(APIView):
    permission_classes = [require_permission("user:manage")]

    @extend_schema(summary="管理员查询用户")
    def get(self, request):
        queryset = (
            User.objects.prefetch_related("roles").filter(is_deleted=False).order_by("-created_at")
        )
        keyword = request.query_params.get("keyword", "").strip()
        if keyword:
            from django.db.models import Q

            queryset = queryset.filter(
                Q(student_no__icontains=keyword)
                | Q(real_name__icontains=keyword)
                | Q(nickname__icontains=keyword)
            )
        role = request.query_params.get("role", "").strip()
        if role:
            queryset = queryset.filter(roles__code=role).distinct()
        status_value = request.query_params.get("status", "").strip()
        if status_value in {"0", "1"}:
            queryset = queryset.filter(status=int(status_value))
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginated(
            paginator,
            UserSerializer(page, many=True, context={"request": request}).data,
            request=request,
        )


class AdminUserDetailView(APIView):
    permission_classes = [require_permission("user:manage")]

    def get_object(self, pk):
        try:
            return User.objects.prefetch_related("roles").get(pk=pk, is_deleted=False)
        except User.DoesNotExist as exc:
            raise BusinessError("用户不存在", 20004, status.HTTP_404_NOT_FOUND) from exc

    @extend_schema(summary="管理员更新用户状态与角色")
    def patch(self, request, pk):
        user = self.get_object(pk)
        serializer = AdminUserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_user_by_admin(user, serializer.validated_data, request.user)
        user.refresh_from_db()
        return success(
            UserSerializer(user, context={"request": request}).data,
            "用户信息已更新",
            request,
        )


class RoleListView(APIView):
    permission_classes = [require_permission("user:manage")]

    @extend_schema(summary="角色字典")
    def get(self, request):
        roles = Role.objects.filter(is_active=True).all()
        return success(RoleBriefSerializer(roles, many=True).data, request=request)
