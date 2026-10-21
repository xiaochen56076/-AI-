from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from common.api.responses import success


class HealthView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(exclude=True)
    def get(self, request):
        return success(
            {
                "status": "ok",
                "service": "CampusHub API",
                "time": timezone.now().isoformat(),
            },
            request=request,
        )
