from django.contrib import admin

from .models import CheckinRecord, Signup


@admin.register(Signup)
class SignupAdmin(admin.ModelAdmin):
    list_display = ("activity", "user", "status", "queue_no", "signup_at")
    list_filter = ("status",)
    search_fields = ("user__student_no", "user__real_name", "activity__title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CheckinRecord)
class CheckinRecordAdmin(admin.ModelAdmin):
    list_display = ("activity", "user", "method", "checkin_at", "operator")
    list_filter = ("method",)
    search_fields = ("user__student_no", "user__real_name", "activity__title")
    readonly_fields = ("signup", "activity", "user", "method", "checkin_at")
