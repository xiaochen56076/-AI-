from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    type_text = serializers.CharField(source="get_type_display", read_only=True)
    activity_id = serializers.IntegerField(read_only=True, allow_null=True)
    activity_title = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "type_text",
            "title",
            "content",
            "activity_id",
            "activity_title",
            "is_read",
            "read_at",
            "created_at",
        ]

    def get_activity_title(self, obj):
        return obj.activity.title if obj.activity_id else None
