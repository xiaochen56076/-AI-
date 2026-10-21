from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "type", "is_read", "created_at")
    list_filter = ("type", "is_read")
    search_fields = ("title", "content", "user__student_no", "user__real_name")
    readonly_fields = ("created_at", "read_at")
