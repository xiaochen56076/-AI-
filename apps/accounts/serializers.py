from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Permission, Role, User


class RoleBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["code", "name"]


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["codename", "name", "resource", "action"]


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    roles = RoleBriefSerializer(many=True, read_only=True)
    permissions = serializers.SerializerMethodField()
    last_login_at = serializers.DateTimeField(source="last_login", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "student_no",
            "real_name",
            "nickname",
            "display_name",
            "avatar_url",
            "email",
            "phone",
            "college",
            "major",
            "grade",
            "status",
            "roles",
            "permissions",
            "is_staff",
            "last_login_at",
            "created_at",
        ]

    def get_permissions(self, obj):
        return sorted(obj.permission_codenames())


class RegisterSerializer(serializers.Serializer):
    student_no = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=8, max_length=64)
    confirm_password = serializers.CharField(write_only=True, max_length=64)
    real_name = serializers.CharField(max_length=50)
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    college = serializers.CharField(max_length=100, required=False, allow_blank=True)
    major = serializers.CharField(max_length=100, required=False, allow_blank=True)
    grade = serializers.IntegerField(
        required=False, allow_null=True, min_value=2000, max_value=2100
    )

    def validate_student_no(self, value):
        value = value.strip()
        if not value.isalnum():
            raise serializers.ValidationError("学号只能包含字母和数字")
        if User.objects.filter(student_no=value).exists():
            raise serializers.ValidationError("该学号已注册")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "两次输入的密码不一致"})
        probe = User(
            student_no=attrs.get("student_no", ""),
            real_name=attrs.get("real_name", ""),
            email=attrs.get("email", ""),
        )
        validate_password(attrs["password"], probe)
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["nickname", "avatar_url", "email", "phone", "college", "major", "grade"]

    def validate_avatar_url(self, value):
        if value and not value.startswith(("http://", "https://")):
            raise serializers.ValidationError("头像地址必须为 http(s) URL")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8, max_length=64)
    confirm_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("原密码不正确")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "两次输入的新密码不一致"})
        validate_password(attrs["new_password"], self.context["request"].user)
        return attrs


class CampusTokenObtainSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "学号或密码不正确",
    }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["roles"] = list(user.roles.filter(is_active=True).values_list("code", flat=True))
        token["name"] = user.display_name
        return token


class AdminUserUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=User.Status.choices, required=False)
    roles = serializers.ListField(
        child=serializers.CharField(max_length=32), required=False, allow_empty=False
    )

    def validate_roles(self, value):
        existing = set(
            Role.objects.filter(code__in=value, is_active=True).values_list("code", flat=True)
        )
        missing = set(value) - existing
        if missing:
            raise serializers.ValidationError(f"角色不存在: {', '.join(sorted(missing))}")
        return value
