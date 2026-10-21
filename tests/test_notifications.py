from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.accounts.services import issue_tokens
from apps.activities.models import Activity, ActivityCategory, AuditRecord
from apps.activities.services import review_activity, submit_activity
from apps.clubs.models import Club
from apps.notifications.models import Notification
from apps.notifications.services import notify
from apps.notifications.tasks import send_activity_reminders
from apps.signups.models import Signup

pytestmark = pytest.mark.django_db


def make_student(number, college="计算机学院", grade=2026):
    user = User.objects.create_user(
        student_no=f"2028{number:04d}",
        password="CampusHub123",
        real_name=f"通知学生{number}",
        college=college,
        grade=grade,
    )
    user.roles.add(Role.objects.get(code="STUDENT"))
    return user


def client_for(user):
    client = APIClient()
    token = issue_tokens(user)["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def make_activity(organizer, **overrides):
    now = timezone.now()
    start = now + timedelta(days=2)
    values = {
        "club": Club.objects.create(name="通知测试社团", owner=organizer),
        "organizer": organizer,
        "category": ActivityCategory.objects.get(slug="lecture"),
        "title": "通知测试活动",
        "summary": "通知功能测试",
        "location": "学术报告厅",
        "start_time": start,
        "end_time": start + timedelta(hours=2),
        "signup_start": now - timedelta(hours=1),
        "signup_end": start - timedelta(hours=2),
        "capacity": 2,
        "waitlist_enabled": True,
        "waitlist_limit": 5,
        "checkin_mode": Activity.CheckinMode.DYNAMIC,
        "status": Activity.Status.PUBLISHED,
    }
    values.update(overrides)
    return Activity.objects.create(**values)


def sign_up(client, activity):
    response = client.post(
        f"/api/v1/activities/{activity.pk}/signup", {}, format="json"
    )
    assert response.status_code == 200, response.content
    return response.json()["data"]


def test_signup_waitlist_and_promotion_create_notifications(
    student_user, organizer_user, auth_client
):
    activity = make_activity(organizer_user, capacity=1)
    sign_up(auth_client, activity)
    success_note = Notification.objects.get(
        user=student_user, type=Notification.Type.SIGNUP_SUCCESS
    )
    assert activity.title in success_note.content

    second = make_student(1)
    second_client = client_for(second)
    sign_up(second_client, activity)
    waitlist_note = Notification.objects.get(
        user=second, type=Notification.Type.WAITLIST_JOINED
    )
    assert "第 1 位" in waitlist_note.content

    assert auth_client.delete(f"/api/v1/activities/{activity.pk}/signup").status_code == 200
    promoted_note = Notification.objects.get(
        user=second, type=Notification.Type.WAITLIST_PROMOTED
    )
    assert activity.title in promoted_note.content
    assert second.notifications.filter(is_read=False).count() == 2


def test_cancelling_activity_notifies_active_signups(
    organizer_user, student_user, organizer_client, auth_client
):
    activity = make_activity(organizer_user)
    sign_up(auth_client, activity)
    second = make_student(2)
    sign_up(client_for(second), activity)

    response = organizer_client.post(
        f"/api/v1/activities/{activity.pk}/cancel",
        {"reason": "场地临时调整"},
        format="json",
    )
    assert response.status_code == 200

    notes = Notification.objects.filter(
        type=Notification.Type.ACTIVITY_CANCELLED, activity=activity
    )
    assert notes.count() == 2
    assert set(notes.values_list("user_id", flat=True)) == {student_user.pk, second.pk}
    assert all("场地临时调整" in note.content for note in notes)


def test_audit_result_notifies_organizer(organizer_user, auditor_user):
    activity = make_activity(organizer_user, status=Activity.Status.DRAFT)
    submit_activity(activity.pk, organizer_user)
    review_activity(activity.pk, auditor_user, AuditRecord.Action.APPROVE, "内容合规")
    approved = Notification.objects.get(
        user=organizer_user, type=Notification.Type.ACTIVITY_AUDITED
    )
    assert approved.title == "活动审核通过"

    rejected_activity = make_activity(
        organizer_user,
        status=Activity.Status.DRAFT,
        title="被驳回的活动",
        club=Club.objects.create(name="另一个社团", owner=organizer_user),
    )
    submit_activity(rejected_activity.pk, organizer_user)
    review_activity(
        rejected_activity.pk, auditor_user, AuditRecord.Action.REJECT, "缺少安全预案"
    )
    rejected = Notification.objects.filter(
        user=organizer_user,
        type=Notification.Type.ACTIVITY_AUDITED,
        activity=rejected_activity,
    ).get()
    assert rejected.title == "活动审核未通过"
    assert "缺少安全预案" in rejected.content


def test_notification_list_unread_and_read_actions(student_user, auth_client):
    for index in range(3):
        notify(
            student_user,
            Notification.Type.SYSTEM,
            f"系统通知 {index}",
            f"内容 {index}",
        )
    other = make_student(9)
    other_note = notify(other, Notification.Type.SYSTEM, "别人的通知", "内容")
    target = Notification.objects.filter(user=student_user, title="系统通知 1").get()

    listed = auth_client.get("/api/v1/notifications")
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 3

    unread = auth_client.get("/api/v1/notifications/unread-count")
    assert unread.json()["data"]["unread"] == 3

    read = auth_client.post(f"/api/v1/notifications/{target.pk}/read")
    assert read.status_code == 200
    assert read.json()["data"]["unread"] == 2
    target.refresh_from_db()
    assert target.is_read is True
    assert target.read_at is not None

    forbidden = auth_client.post(f"/api/v1/notifications/{other_note.pk}/read")
    assert forbidden.status_code == 404

    unread_list = auth_client.get("/api/v1/notifications", {"status": "unread"})
    assert unread_list.json()["data"]["total"] == 2

    read_all = auth_client.post("/api/v1/notifications/read-all")
    assert read_all.status_code == 200
    assert read_all.json()["data"]["unread"] == 0
    assert Notification.objects.filter(user=student_user, is_read=False).count() == 0


def test_activity_reminders_are_idempotent_and_skip_checked_in(
    organizer_user, auth_client, student_user
):
    now = timezone.now()
    activity = make_activity(
        organizer_user,
        start_time=now + timedelta(minutes=90),
        end_time=now + timedelta(hours=3),
        signup_end=now + timedelta(minutes=30),
    )
    sign_up(auth_client, activity)
    checked_in = make_student(3)
    Signup.objects.create(
        activity=activity, user=checked_in, status=Signup.Status.CHECKED_IN
    )

    first = send_activity_reminders(now=now)
    assert first == {"activities": 1, "notifications": 1}
    second = send_activity_reminders(now=now)
    assert second == {"activities": 1, "notifications": 0}

    reminders = Notification.objects.filter(type=Notification.Type.ACTIVITY_REMINDER)
    assert reminders.count() == 1
    assert reminders.get().user_id == student_user.pk
    assert "签到" in reminders.get().content


def test_close_expired_activity_marks_no_show_and_cancels_waitlist(organizer_user):
    from apps.activities.tasks import close_expired_activities

    now = timezone.now()
    activity = make_activity(
        organizer_user,
        start_time=now - timedelta(hours=2),
        end_time=now - timedelta(hours=1),
        signup_start=now - timedelta(days=1),
        signup_end=now - timedelta(hours=3),
        capacity=1,
    )
    first, second = make_student(4), make_student(5)
    Signup.objects.create(activity=activity, user=first, status=Signup.Status.SUCCESS)
    Signup.objects.create(
        activity=activity, user=second, status=Signup.Status.WAITLIST, queue_no=1
    )
    Activity.objects.filter(pk=activity.pk).update(signup_count=1, waitlist_count=1)

    stats = close_expired_activities(now=now)
    assert stats == {"activities": 1, "no_shows": 1, "waitlist_cancelled": 1}
    activity.refresh_from_db()
    assert activity.status == Activity.Status.ENDED
    assert activity.waitlist_count == 0
    assert Signup.objects.get(activity=activity, user=first).status == Signup.Status.NO_SHOW
    assert (
        Signup.objects.get(activity=activity, user=second).status
        == Signup.Status.CANCELLED
    )
    assert close_expired_activities(now=now)["activities"] == 0

    no_checkin = make_activity(
        organizer_user,
        title="无需签到活动",
        checkin_mode=Activity.CheckinMode.NONE,
        start_time=now - timedelta(hours=2),
        end_time=now - timedelta(hours=1),
        signup_start=now - timedelta(days=1),
        signup_end=now - timedelta(hours=3),
    )
    Signup.objects.create(
        activity=no_checkin, user=make_student(6), status=Signup.Status.SUCCESS
    )
    close_expired_activities(now=now)
    assert Signup.objects.get(activity=no_checkin).status == Signup.Status.SUCCESS
