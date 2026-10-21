from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.IntegerChoices):
        SYSTEM = 0, "系统通知"
        SIGNUP_SUCCESS = 1, "报名成功"
        WAITLIST_JOINED = 2, "候补中"
        WAITLIST_PROMOTED = 3, "候补转正"
        ACTIVITY_REMINDER = 4, "活动提醒"
        ACTIVITY_CANCELLED = 5, "活动取消"
        ACTIVITY_AUDITED = 6, "审核结果"
        CHECKIN_SUCCESS = 7, "签到成功"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    activity = models.ForeignKey(
        "activities.Activity",
        on_delete=models.SET_NULL,
        related_name="notifications",
        null=True,
        blank=True,
    )
    type = models.SmallIntegerField(choices=Type.choices, default=Type.SYSTEM)
    title = models.CharField(max_length=120)
    content = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    dedupe_key = models.CharField(max_length=128, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "is_read"], name="idx_notification_user_read"),
            models.Index(fields=["user", "created_at"], name="idx_notification_user_time"),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.title}"
