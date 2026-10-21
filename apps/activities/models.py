import secrets

from django.conf import settings
from django.db import models

from apps.clubs.models import Club


class ActivityCategory(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)
    icon = models.CharField(max_length=32, blank=True, default="Calendar")
    color = models.CharField(max_length=20, blank=True, default="#3B6BFA")
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "activity_category"
        ordering = ["sort_order", "id"]
        verbose_name_plural = "activity categories"

    def __str__(self):
        return self.name


class ActivityTag(models.Model):
    name = models.CharField(max_length=32, unique=True)
    color = models.CharField(max_length=20, blank=True, default="#5B6B8C")
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "activity_tag"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Activity(models.Model):
    class Status(models.IntegerChoices):
        DRAFT = 0, "草稿"
        PENDING = 1, "待审核"
        PUBLISHED = 2, "已发布"
        ENDED = 3, "已结束"
        CANCELLED = 4, "已取消"
        REJECTED = 5, "已驳回"

    class CheckinMode(models.IntegerChoices):
        NONE = 0, "无需签到"
        STATIC = 1, "静态码"
        DYNAMIC = 2, "动态码"

    club = models.ForeignKey(Club, on_delete=models.PROTECT, related_name="activities")
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="organized_activities"
    )
    category = models.ForeignKey(
        ActivityCategory, on_delete=models.PROTECT, related_name="activities"
    )
    tags = models.ManyToManyField(
        ActivityTag, through="ActivityTagRel", related_name="activities", blank=True
    )
    title = models.CharField(max_length=120)
    summary = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    cover_url = models.URLField(max_length=500, blank=True, default="")
    location = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    signup_start = models.DateTimeField()
    signup_end = models.DateTimeField()
    capacity = models.PositiveIntegerField()
    waitlist_enabled = models.BooleanField(default=True)
    waitlist_limit = models.PositiveIntegerField(default=0)
    checkin_mode = models.SmallIntegerField(
        choices=CheckinMode.choices, default=CheckinMode.DYNAMIC
    )
    checkin_secret = models.CharField(max_length=64, blank=True, default="")
    status = models.SmallIntegerField(choices=Status.choices, default=Status.DRAFT)
    signup_count = models.PositiveIntegerField(default=0)
    waitlist_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    cancel_reason = models.CharField(max_length=255, blank=True, default="")
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "activity"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "start_time"], name="idx_status_start"),
            models.Index(fields=["category"], name="idx_category"),
            models.Index(fields=["organizer"], name="idx_organizer"),
            models.Index(fields=["club"], name="idx_club"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gt=0), name="chk_activity_capacity"
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.checkin_secret:
            self.checkin_secret = secrets.token_hex(32)
        super().save(*args, **kwargs)

    @property
    def remaining(self):
        return max(self.capacity - self.signup_count, 0)

    @property
    def is_signup_open(self):
        from django.utils import timezone

        now = timezone.now()
        return (
            self.status == self.Status.PUBLISHED
            and self.signup_start <= now <= self.signup_end
            and self.signup_count < self.capacity
        )

    def __str__(self):
        return self.title


class ActivityTagRel(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    tag = models.ForeignKey(ActivityTag, on_delete=models.CASCADE)

    class Meta:
        db_table = "activity_tag_rel"
        unique_together = ("activity", "tag")


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites"
    )
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "favorite"
        unique_together = ("user", "activity")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} -> {self.activity_id}"


class AuditRecord(models.Model):
    class Action(models.IntegerChoices):
        APPROVE = 1, "通过"
        REJECT = 2, "驳回"

    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="audit_records")
    auditor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="audit_records"
    )
    action = models.SmallIntegerField(choices=Action.choices)
    comment = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_record"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.activity_id}:{self.get_action_display()}"
