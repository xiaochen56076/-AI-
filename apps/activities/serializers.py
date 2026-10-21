from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import User
from apps.clubs.models import Club

from .models import Activity, ActivityCategory, ActivityTag, AuditRecord


class ClubBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ["id", "name", "logo_url"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityCategory
        fields = ["id", "name", "slug", "icon", "color", "sort_order"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityTag
        fields = ["id", "name", "color"]


class OrganizerBriefSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "real_name", "display_name", "college", "avatar_url"]


class ActivityBriefSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    club = ClubBriefSerializer(read_only=True)
    organizer = OrganizerBriefSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    status_text = serializers.CharField(source="get_status_display", read_only=True)
    checkin_mode_text = serializers.CharField(source="get_checkin_mode_display", read_only=True)
    remaining = serializers.IntegerField(read_only=True)
    is_signup_open = serializers.BooleanField(read_only=True)
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            "id",
            "title",
            "summary",
            "cover_url",
            "location",
            "start_time",
            "end_time",
            "signup_start",
            "signup_end",
            "capacity",
            "signup_count",
            "waitlist_count",
            "remaining",
            "waitlist_enabled",
            "waitlist_limit",
            "checkin_mode",
            "checkin_mode_text",
            "status",
            "status_text",
            "view_count",
            "is_signup_open",
            "is_favorited",
            "category",
            "tags",
            "club",
            "organizer",
            "created_at",
        ]

    def get_is_favorited(self, obj):
        return bool(getattr(obj, "is_favorited_flag", False))


class AuditRecordSerializer(serializers.ModelSerializer):
    auditor_name = serializers.CharField(source="auditor.display_name", read_only=True)
    action_text = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = AuditRecord
        fields = ["id", "action", "action_text", "comment", "auditor_name", "created_at"]


class ActivityDetailSerializer(ActivityBriefSerializer):
    can_manage = serializers.SerializerMethodField()
    can_submit = serializers.SerializerMethodField()
    can_audit = serializers.SerializerMethodField()
    audit_records = serializers.SerializerMethodField()

    class Meta(ActivityBriefSerializer.Meta):
        fields = [
            *ActivityBriefSerializer.Meta.fields,
            "description",
            "checkin_secret",
            "cancel_reason",
            "updated_at",
            "can_manage",
            "can_submit",
            "can_audit",
            "audit_records",
        ]

    def _user(self):
        request = self.context.get("request")
        return getattr(request, "user", None)

    def get_can_manage(self, obj):
        user = self._user()
        return bool(user and user.is_authenticated and obj.organizer_id == user.id)

    def get_can_submit(self, obj):
        return self.get_can_manage(obj) and obj.status in {
            Activity.Status.DRAFT,
            Activity.Status.REJECTED,
        }

    def get_can_audit(self, obj):
        from common.permissions import user_has_permission

        user = self._user()
        return bool(
            user
            and user.is_authenticated
            and obj.status == Activity.Status.PENDING
            and user_has_permission(user, "activity:audit")
        )

    def get_audit_records(self, obj):
        if not (self.get_can_manage(obj) or self.get_can_audit(obj)):
            return []
        records = obj.audit_records.select_related("auditor").all()[:20]
        return AuditRecordSerializer(records, many=True).data

    def get_checkin_secret(self, obj):
        if not self.get_can_manage(obj):
            return None
        return obj.checkin_secret


class ActivityWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=120)
    summary = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    description = serializers.CharField(required=False, allow_blank=True, default="")
    cover_url = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    location = serializers.CharField(max_length=200)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    signup_start = serializers.DateTimeField()
    signup_end = serializers.DateTimeField()
    capacity = serializers.IntegerField(min_value=1, max_value=100000)
    waitlist_enabled = serializers.BooleanField(required=False, default=True)
    waitlist_limit = serializers.IntegerField(
        min_value=0, max_value=100000, required=False, default=0
    )
    checkin_mode = serializers.ChoiceField(
        choices=Activity.CheckinMode.choices, required=False, default=2
    )
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=ActivityCategory.objects.filter(is_active=True, is_deleted=False),
    )
    club_id = serializers.PrimaryKeyRelatedField(
        source="club",
        queryset=Club.objects.filter(is_active=True, is_deleted=False),
        required=False,
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        source="tags",
        queryset=ActivityTag.objects.filter(is_active=True, is_deleted=False),
        many=True,
        required=False,
    )

    def validate_cover_url(self, value):
        if value and not value.startswith(("http://", "https://", "/")):
            raise serializers.ValidationError("封面地址必须为 http(s) URL 或站内绝对路径")
        return value

    def _current(self, attrs, field):
        if field in attrs:
            return attrs[field]
        if self.instance is not None:
            return getattr(self.instance, field)
        return None

    def validate(self, attrs):
        start_time = self._current(attrs, "start_time")
        end_time = self._current(attrs, "end_time")
        signup_start = self._current(attrs, "signup_start")
        signup_end = self._current(attrs, "signup_end")
        capacity = self._current(attrs, "capacity")
        waitlist_limit = self._current(attrs, "waitlist_limit")

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "结束时间必须晚于开始时间"})
        if signup_start and signup_end and signup_end <= signup_start:
            raise serializers.ValidationError({"signup_end": "报名截止时间必须晚于报名开始时间"})
        if signup_end and start_time and signup_end > start_time:
            raise serializers.ValidationError({"signup_end": "报名截止时间不能晚于活动开始时间"})
        if end_time and end_time <= timezone.now():
            raise serializers.ValidationError({"end_time": "结束时间必须晚于当前时间"})
        if capacity is not None and capacity < 1:
            raise serializers.ValidationError({"capacity": "活动容量至少为 1"})
        if waitlist_limit and capacity and waitlist_limit > capacity * 10:
            raise serializers.ValidationError({"waitlist_limit": "候补上限不能超过容量的 10 倍"})
        return attrs


class CancelActivitySerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class AuditActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=AuditRecord.Action.choices)
    comment = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
