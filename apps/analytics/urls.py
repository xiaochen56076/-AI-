from django.urls import path

from .views import ActivityStatisticsView, GlobalDashboardView

urlpatterns = [
    path(
        "activities/<int:pk>/statistics",
        ActivityStatisticsView.as_view(),
        name="activity-statistics",
    ),
    path("admin/dashboard", GlobalDashboardView.as_view(), name="admin-dashboard"),
]
