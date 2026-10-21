from rest_framework import serializers

from apps.activities.models import Activity
from apps.activities.serializers import ActivityBriefSerializer

from .models import Signup


class SignupStudentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    student_no = serializers.CharField(read_only=True)
    real_name = serializers.CharField(read_only=True)
    nickname = serializers.CharField(read_only=True)
    college = serializers.CharField(read_only=True)
    major = serializers.CharField(read_only=True)
    grade = serializers.IntegerField(read_only=True, allow_null=True)
    avatar_url = serializers.URLField(read_only=True)


class SignupSerializer(serializers.ModelSerializer):
    user = SignupStudentSerializer(read_only=True)
    status_text = serializers.CharField(source="get_status_display", read_only=True)
    queue_position = serializers.SerializerMethodField()
    checked_in_at = serializers.SerializerMethodField()
    checkin_method = serializers.SerializerMethodField()
    checkin_method_text = serializers.SerializerMethodField()

    class Meta:
        model = Signup
        fields = [
            "id",
            "status",
            "status_text",
            "queue_no",
            "queue_position",
            "remark",
            "signup_at",
            "cancel_at",
            "checked_in_at",
            "checkin_method",
            "checkin_method_text",
            "user",
        ]

    def get_queue_position(self, obj):
        if obj.status != Signup.Status.WAITLIST:
            return None
        return (
            Signup.objects.filter(
                activity_id=obj.activity_id,
                status=Signup.Status.WAITLIST,
                queue_no__lt=obj.queue_no or 0,
            ).count()
            + 1
        )

    def _record(self, obj):
        try:
            return obj.checkin_record
        except Exception:
            return None

    def get_checked_in_at(self, obj):
        record = self._record(obj)
        return record.checkin_at.isoformat() if record else None

    def get_checkin_method(self, obj):
        record = self._record(obj)
        return record.method if record else None

    def get_checkin_method_text(self, obj):
        record = self._record(obj)
        return record.get_method_display() if record else None


class MySignupSerializer(serializers.ModelSerializer):
    activity = ActivityBriefSerializer(read_only=True)
    status_text = serializers.CharField(source="get_status_display", read_only=True)
    queue_position = serializers.SerializerMethodField()
    checked_in_at = serializers.SerializerMethodField()

    class Meta:
        model = Signup
        fields = [
            "id",
            "status",
            "status_text",
            "queue_no",
            "queue_position",
            "signup_at",
            "cancel_at",
            "checked_in_at",
            "activity",
        ]

    def get_queue_position(self, obj):
        if obj.status != Signup.Status.WAITLIST:
            return None
        return (
            Signup.objects.filter(
                activity_id=obj.activity_id,
                status=Signup.Status.WAITLIST,
                queue_no__lt=obj.queue_no or 0,
            ).count()
            + 1
        )

    def get_checked_in_at(self, obj):
        record = getattr(obj, "checkin_record", None)
        return record.checkin_at.isoformat() if record else None


class CheckinRequestSerializer(serializers.Serializer):
    activity_id = serializers.IntegerField(min_value=1)
    code = serializers.CharField(max_length=16)
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    device_info = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class ManualCheckinSerializer(serializers.Serializer):
    student_no = serializers.CharField(max_length=20)
    reason = serializers.CharField(max_length=255, min_length=2)


def serialize_signup_result(signup: Signup, request=None):
    activity = signup.activity
    fresh = Activity.objects.filter(pk=activity.pk).values(
        "signup_count", "waitlist_count", "capacity"
    )[0]
    return {
        "signup_id": signup.pk,
        "status": signup.status,
        "status_text": signup.status_text,
        "activity_id": signup.activity_id,
        "remaining": max(fresh["capacity"] - fresh["signup_count"], 0),
        "position": SignupSerializer().get_queue_position(signup),
    }
