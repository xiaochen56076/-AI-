from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Role, User


@transaction.atomic
def register_student(validated_data: dict) -> User:
    roles_data = validated_data.pop("roles", None)
    user = User.objects.create_user(**validated_data)
    student_role = Role.objects.filter(code=User.RoleCode.STUDENT).first()
    if student_role:
        user.roles.add(student_role)
    if roles_data:
        set_user_roles(user, roles_data)
    return user


def issue_tokens(user: User, request=None) -> dict:
    refresh = RefreshToken.for_user(user)
    refresh["roles"] = list(user.roles.filter(is_active=True).values_list("code", flat=True))
    refresh["name"] = user.display_name
    access = refresh.access_token
    access["roles"] = refresh["roles"]
    access["name"] = refresh["name"]
    from .serializers import UserSerializer

    return {
        "access": str(access),
        "refresh": str(refresh),
        "expires_in": int(access.lifetime.total_seconds()),
        "user": UserSerializer(user, context={"request": request}).data,
    }


@transaction.atomic
def set_user_roles(user: User, role_codes: list[str]) -> User:
    roles = list(Role.objects.filter(code__in=role_codes, is_active=True))
    found = {role.code for role in roles}
    missing = set(role_codes) - found
    if missing:
        raise ValidationError({"roles": f"角色不存在: {', '.join(sorted(missing))}"})
    if not roles:
        raise ValidationError({"roles": "用户至少需要一个角色"})
    user.roles.set(roles)
    return user


@transaction.atomic
def update_user_by_admin(user: User, validated_data: dict, operator: User) -> User:
    new_status = validated_data.get("status")
    if user.pk == operator.pk and new_status == User.Status.DISABLED:
        raise ValidationError({"status": "不能禁用当前登录账号"})
    role_codes = validated_data.pop("roles", None)
    for field, value in validated_data.items():
        setattr(user, field, value)
    user.save()
    if role_codes is not None:
        if user.pk == operator.pk and User.RoleCode.ADMIN not in role_codes:
            raise ValidationError({"roles": "不能移除自己的管理员角色"})
        set_user_roles(user, role_codes)
    return user
