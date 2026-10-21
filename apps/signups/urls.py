from django.urls import path

from .views import (
    ActivitySignupExportView,
    ActivitySignupListView,
    ActivitySignupView,
    MySignupsView,
)

urlpatterns = [
    path("activities/<int:pk>/signup", ActivitySignupView.as_view(), name="activity-signup"),
    path(
        "activities/<int:pk>/signups",
        ActivitySignupListView.as_view(),
        name="activity-signup-list",
    ),
    path(
        "activities/<int:pk>/signups/export",
        ActivitySignupExportView.as_view(),
        name="activity-signup-export",
    ),
    path("my/signups", MySignupsView.as_view(), name="my-signups"),
]
