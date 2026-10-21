from django.conf import settings
from django.db import models

from apps.activities.models import Activity


class Signup(models.Model):
    class Status(models.IntegerChoices):
        WAITLIST = 0, "候补中"
        SUCCESS = 1, "报名成功"
        CANCELLED = 2, "已取消"
        CHECKED_IN = 3, "已签到"
        NO_SHOW = 4, "已爽约"

    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="signups")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="signups"
    )
    status = models.SmallIntegerField(choices=Status.choices, default=Status.SUCCESS)
    queue_no = models.IntegerField(null=True, blank=True)
    remark = models.CharField(max_length=255, blank=True, default="")
    signup_at = models.DateTimeField(auto_now_add=True)
    cancel_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "signup"
        ordering = ["-signup_at"]
        constraints = [
            models.UniqueConstraint(fields=["activity", "user"], name="uk_activity_user"),
        ]
        indexes = [
            models.Index(fields=["user", "status"], name="idx_user_status"),
            models.Index(fields=["activity", "status"], name="idx_activity_status"),
        ]

    @property
    def status_text(self):
        return self.get_status_display()

    def __str__(self):
        return f"{self.user_id}@{self.activity_id}:{self.get_status_display()}"
