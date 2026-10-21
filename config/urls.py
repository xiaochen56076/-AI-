from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from common.views import HealthView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health", HealthView.as_view(), name="health"),
    path("api/v1/schema", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/v1/docs",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.activities.urls")),
]

handler404 = "common.exceptions.api_not_found_view"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
