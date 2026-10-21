from rest_framework.permissions import BasePermission


def user_has_permission(user, codename: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user.roles.filter(is_active=True, permissions__codename=codename).exists()


class HasPermission(BasePermission):
    required_permission = ""
    message = "没有执行此操作的权限"

    def has_permission(self, request, view):
        return user_has_permission(request.user, self.required_permission)


def require_permission(codename: str):
    return type(
        f"Require_{codename.replace(':', '_')}",
        (HasPermission,),
        {"required_permission": codename},
    )
