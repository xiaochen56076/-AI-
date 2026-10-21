from django.conf import settings
from django.db import models


class Club(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, default="")
    logo_url = models.URLField(max_length=255, blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owned_clubs",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "club"
        ordering = ["id"]

    def __str__(self):
        return self.name
