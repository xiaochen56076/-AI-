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


class MySignupSerializer(serializers.ModelSerializer):
    activity = ActivityBriefSerializer(read_only=True)
    status_text = serializers.CharField(source="get_status_display", read_only=True)
    queue_position = serializers.SerializerMethodField()

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
