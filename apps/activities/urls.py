from django.urls import path

from .views import (
    ActivityCancelView,
    ActivityDetailView,
    ActivityFavoriteView,
    ActivityListCreateView,
    ActivitySubmitView,
    AdminAuditActionView,
    AdminAuditListView,
    CategoryListView,
    MyActivitiesView,
    MyFavoritesView,
    TagListView,
)

urlpatterns = [
    path("categories", CategoryListView.as_view(), name="activity-categories"),
    path("tags", TagListView.as_view(), name="activity-tags"),
    path("activities", ActivityListCreateView.as_view(), name="activities"),
    path("activities/<int:pk>", ActivityDetailView.as_view(), name="activity-detail"),
    path("activities/<int:pk>/submit", ActivitySubmitView.as_view(), name="activity-submit"),
    path("activities/<int:pk>/cancel", ActivityCancelView.as_view(), name="activity-cancel"),
    path("activities/<int:pk>/favorite", ActivityFavoriteView.as_view(), name="activity-favorite"),
    path("my/activities", MyActivitiesView.as_view(), name="my-activities"),
    path("my/favorites", MyFavoritesView.as_view(), name="my-favorites"),
    path("admin/audits", AdminAuditListView.as_view(), name="admin-audits"),
    path("admin/audits/<int:pk>", AdminAuditActionView.as_view(), name="admin-audit-action"),
]
