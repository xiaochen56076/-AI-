from django.contrib import admin

from .models import Signup


@admin.register(Signup)
class SignupAdmin(admin.ModelAdmin):
    list_display = ("activity", "user", "status", "queue_no", "signup_at")
    list_filter = ("status",)
    search_fields = ("user__student_no", "user__real_name", "activity__title")
    readonly_fields = ("created_at", "updated_at")
