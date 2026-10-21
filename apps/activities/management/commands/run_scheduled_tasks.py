from django.core.management.base import BaseCommand

from apps.activities.tasks import close_expired_activities
from apps.notifications.tasks import send_activity_reminders


class Command(BaseCommand):
    help = "结束过期活动、标记爽约并发送开场提醒（无 Celery 环境下的本地调度入口）"

    def handle(self, *args, **options):
        closed = close_expired_activities()
        reminders = send_activity_reminders()
        self.stdout.write(
            self.style.SUCCESS(
                f"活动结束 {closed['activities']} 场，爽约 {closed['no_shows']} 人，"
                f"取消候补 {closed['waitlist_cancelled']} 人；"
                f"提醒 {reminders['activities']} 场活动，新增 {reminders['notifications']} 条通知。"
            )
        )
