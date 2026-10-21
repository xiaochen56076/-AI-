from django.urls import path

from .views import (
    AdminUserDetailView,
    AdminUserListView,
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    RegisterView,
    RoleListView,
)

urlpatterns = [
    path("auth/register", RegisterView.as_view(), name="auth-register"),
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/refresh", RefreshView.as_view(), name="auth-refresh"),
    path("auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("users/me", MeView.as_view(), name="user-me"),
    path("users/me/password", ChangePasswordView.as_view(), name="user-password"),
    path("admin/users", AdminUserListView.as_view(), name="admin-users"),
    path("admin/users/<int:pk>", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("admin/roles", RoleListView.as_view(), name="admin-roles"),
]
