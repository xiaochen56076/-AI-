from django.contrib import admin

from .models import Activity, ActivityCategory, ActivityTag, AuditRecord, Favorite


@admin.register(ActivityCategory)
class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    search_fields = ("name", "slug")


@admin.register(ActivityTag)
class ActivityTagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "is_active")
    search_fields = ("name",)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "organizer",
        "status",
        "signup_count",
        "capacity",
        "start_time",
    )
    list_filter = ("status", "category", "checkin_mode")
    search_fields = ("title", "organizer__real_name", "club__name")
    date_hierarchy = "start_time"
    readonly_fields = ("signup_count", "waitlist_count", "view_count", "created_at", "updated_at")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "activity", "created_at")
    search_fields = ("user__student_no", "activity__title")


@admin.register(AuditRecord)
class AuditRecordAdmin(admin.ModelAdmin):
    list_display = ("activity", "auditor", "action", "created_at")
    list_filter = ("action",)
    search_fields = ("activity__title", "auditor__real_name")
