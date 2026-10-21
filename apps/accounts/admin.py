from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import Permission, Role, RolePermission, User, UserRole


class CampusUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("student_no", "real_name")


class CampusUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 0


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = CampusUserCreationForm
    form = CampusUserChangeForm
    ordering = ("-created_at",)
    list_display = ("student_no", "real_name", "status", "is_staff", "created_at")
    list_filter = ("status", "is_staff")
    search_fields = ("student_no", "real_name", "nickname")
    fieldsets = (
        (None, {"fields": ("student_no", "password")}),
        (
            "个人信息",
            {
                "fields": (
                    "real_name",
                    "nickname",
                    "avatar_url",
                    "email",
                    "phone",
                    "college",
                    "major",
                    "grade",
                )
            },
        ),
        ("权限", {"fields": ("is_staff", "is_superuser", "is_deleted")}),
        ("状态", {"fields": ("status", "last_login")}),
    )
    add_fieldsets = (
        (
            None,
            {"classes": ("wide",), "fields": ("student_no", "real_name", "password1", "password2")},
        ),
    )
    inlines = [UserRoleInline]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    inlines = [RolePermissionInline]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("codename", "name", "resource", "action")
