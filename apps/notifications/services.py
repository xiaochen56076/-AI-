from django.utils import timezone

from .models import Notification


def _when(activity) -> str:
    return timezone.localtime(activity.start_time).strftime("%m月%d日 %H:%M")


def notify(user, type, title, content, activity=None, dedupe_key=None):
    values = {
        "user": user,
        "type": type,
        "title": title,
        "content": content[:500],
        "activity": activity,
    }
    if dedupe_key:
        notification, _ = Notification.objects.get_or_create(
            dedupe_key=dedupe_key, defaults=values
        )
        return notification
    return Notification.objects.create(**values)


def notify_signup_result(signup, position=None):
    from apps.signups.models import Signup

    activity = signup.activity
    if signup.status == Signup.Status.SUCCESS:
        return notify(
            signup.user,
            Notification.Type.SIGNUP_SUCCESS,
            "报名成功",
            f"你已成功报名《{activity.title}》，活动时间 {_when(activity)}，"
            f"地点 {activity.location}。请准时参加。",
            activity,
        )
    if signup.status == Signup.Status.WAITLIST:
        suffix = f"，当前排在第 {position} 位" if position else ""
        return notify(
            signup.user,
            Notification.Type.WAITLIST_JOINED,
            "已进入候补队列",
            f"《{activity.title}》名额已满，你已进入候补队列{suffix}。"
            "如有名额释放，系统会自动为你转正。",
            activity,
        )
    return None


def notify_waitlist_promoted(signup):
    activity = signup.activity
    return notify(
        signup.user,
        Notification.Type.WAITLIST_PROMOTED,
        "候补转正通知",
        f"恭喜！《{activity.title}》已有名额释放，你已成功转正。"
        f"活动时间 {_when(activity)}，地点 {activity.location}。",
        activity,
    )


def notify_activity_cancelled(activity, reason, user_ids):
    content = (
        f"很抱歉，《{activity.title}》已取消。原因：{reason.strip() or '主办方未填写'}。"
        "如已报名，无需额外操作。"
    )
    notifications = [
        Notification(
            user_id=user_id,
            activity=activity,
            type=Notification.Type.ACTIVITY_CANCELLED,
            title="活动取消通知",
            content=content,
            dedupe_key=f"cancelled:{activity.pk}:{user_id}",
        )
        for user_id in set(user_ids)
    ]
    if notifications:
        Notification.objects.bulk_create(notifications, ignore_conflicts=True)
    return len(notifications)


def notify_audit_result(activity, approved: bool, comment: str = ""):
    if approved:
        title = "活动审核通过"
        content = f"你的活动《{activity.title}》已通过审核并发布，学生现在可以查看和报名。"
    else:
        title = "活动审核未通过"
        content = f"你的活动《{activity.title}》未通过审核。审核意见：{comment.strip() or '无'}"
    return notify(
        activity.organizer,
        Notification.Type.ACTIVITY_AUDITED,
        title,
        content,
        activity,
    )


def notify_checkin_success(record):
    activity = record.activity
    return notify(
        record.user,
        Notification.Type.CHECKIN_SUCCESS,
        "签到成功",
        f"你已完成《{activity.title}》签到，签到时间 "
        f"{timezone.localtime(record.checkin_at).strftime('%m月%d日 %H:%M')}。",
        activity,
        dedupe_key=f"checkin:{record.signup_id}",
    )


def notify_activity_reminders(activity, user_ids):
    content = (
        f"《{activity.title}》将于 {_when(activity)} 在 {activity.location} 开始，"
        "请提前到场并打开 CampusHub 扫码签到。"
    )
    keys = {user_id: f"reminder:{activity.pk}:{user_id}" for user_id in set(user_ids)}
    existing = set(
        Notification.objects.filter(dedupe_key__in=keys.values()).values_list(
            "dedupe_key", flat=True
        )
    )
    notifications = [
        Notification(
            user_id=user_id,
            activity=activity,
            type=Notification.Type.ACTIVITY_REMINDER,
            title="活动即将开始",
            content=content,
            dedupe_key=dedupe_key,
        )
        for user_id, dedupe_key in keys.items()
        if dedupe_key not in existing
    ]
    if notifications:
        Notification.objects.bulk_create(notifications, ignore_conflicts=True)
    return len(notifications)
