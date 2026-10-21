from django.urls import path

from .views import (
    ActivityCheckinCodeView,
    ActivitySignupExportView,
    ActivitySignupListView,
    ActivitySignupView,
    CheckinView,
    ManualCheckinView,
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
    path(
        "activities/<int:pk>/checkin-code",
        ActivityCheckinCodeView.as_view(),
        name="activity-checkin-code",
    ),
    path(
        "activities/<int:pk>/checkin-manual",
        ManualCheckinView.as_view(),
        name="activity-checkin-manual",
    ),
    path("checkin", CheckinView.as_view(), name="checkin"),
    path("my/signups", MySignupsView.as_view(), name="my-signups"),
]
