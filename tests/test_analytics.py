from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.activities.models import Activity, ActivityCategory
from apps.clubs.models import Club
from apps.signups.models import CheckinRecord, Signup

pytestmark = pytest.mark.django_db


def make_student(number, college="计算机学院", grade=2026):
    user = User.objects.create_user(
        student_no=f"2029{number:04d}",
        password="CampusHub123",
        real_name=f"统计学生{number}",
        college=college,
        grade=grade,
    )
    user.roles.add(Role.objects.get(code="STUDENT"))
    return user


@pytest.fixture
def statistics_activity(organizer_user):
    now = timezone.now()
    activity = Activity.objects.create(
        club=Club.objects.create(name="统计测试社团", owner=organizer_user),
        organizer=organizer_user,
        category=ActivityCategory.objects.get(slug="lecture"),
        title="数据统计测试讲座",
        summary="统计看板测试",
        location="报告厅",
        start_time=now - timedelta(hours=2),
        end_time=now - timedelta(hours=1),
        signup_start=now - timedelta(days=2),
        signup_end=now - timedelta(hours=3),
        capacity=10,
        checkin_mode=Activity.CheckinMode.DYNAMIC,
        status=Activity.Status.ENDED,
        view_count=100,
    )
    promoted = Signup.objects.create(
        activity=activity,
        user=make_student(1, "计算机学院", 2026),
        status=Signup.Status.SUCCESS,
        queue_no=2,
    )
    checked_in = Signup.objects.create(
        activity=activity,
        user=make_student(2, "艺术学院", 2025),
        status=Signup.Status.CHECKED_IN,
    )
    Signup.objects.create(
        activity=activity,
        user=make_student(3),
        status=Signup.Status.WAITLIST,
        queue_no=1,
    )
    no_show = Signup.objects.create(
        activity=activity,
        user=make_student(4),
        status=Signup.Status.NO_SHOW,
    )
    CheckinRecord.objects.create(
        signup=checked_in,
        activity=activity,
        user=checked_in.user,
        method=CheckinRecord.Method.SCAN,
    )
    Activity.objects.filter(pk=activity.pk).update(signup_count=3, waitlist_count=1)
    activity.signup_count = 3
    activity.waitlist_count = 1
    return activity, promoted, checked_in, no_show


def test_activity_statistics_counts_rates_and_distributions(
    organizer_client, statistics_activity
):
    activity, promoted, checked_in, no_show = statistics_activity

    response = organizer_client.get(f"/api/v1/activities/{activity.pk}/statistics")
    assert response.status_code == 200, response.content
    data = response.json()["data"]

    assert data["counts"]["total"] == 4
    assert data["counts"]["success"] == 3
    assert data["counts"]["checked_in"] == 1
    assert data["counts"]["no_show"] == 1
    assert data["counts"]["waitlist"] == 1
    assert data["counts"]["waitlisted_ever"] == 2
    assert data["counts"]["promoted"] == 1
    assert data["rates"]["fill_rate"] == 0.3
    assert data["rates"]["checkin_rate"] == 0.3333
    assert data["rates"]["waitlist_promotion_rate"] == 0.5
    assert data["rates"]["view_conversion_rate"] == 0.03

    assert data["checkin_method_distribution"] == [{"name": "扫码签到", "value": 1}]
    colleges = {item["name"]: item["value"] for item in data["college_distribution"]}
    assert colleges["计算机学院"] == 2
    assert colleges["艺术学院"] == 1
    grades = {item["name"]: item["value"] for item in data["grade_distribution"]}
    assert grades["2026级"] == 2
    assert grades["2025级"] == 1
    assert len(data["signup_trend"]) == 7
    assert data["signup_trend"][-1]["value"] == 4


def test_statistics_access_control(
    organizer_client,
    another_organizer_client,
    auth_client,
    admin_client,
    statistics_activity,
):
    activity, _, _, _ = statistics_activity
    assert (
        another_organizer_client.get(
            f"/api/v1/activities/{activity.pk}/statistics"
        ).status_code
        == 403
    )
    assert (
        auth_client.get(f"/api/v1/activities/{activity.pk}/statistics").status_code
        == 403
    )
    assert (
        admin_client.get(f"/api/v1/activities/{activity.pk}/statistics").status_code
        == 200
    )


def test_global_dashboard_requires_admin(
    admin_client, organizer_client, auth_client, statistics_activity
):
    assert auth_client.get("/api/v1/admin/dashboard").status_code == 403
    assert organizer_client.get("/api/v1/admin/dashboard").status_code == 403

    response = admin_client.get("/api/v1/admin/dashboard")
    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["totals"]["activities"] >= 1
    assert data["totals"]["signups"] == 4
    assert data["totals"]["checked_in"] == 1
    assert data["totals"]["no_show"] == 1
    assert data["rates"]["checkin_rate"] == 0.3333
    assert len(data["weekly_trend"]) == 8
    assert data["weekly_trend"][-1]["signups"] == 4
    assert any(item["name"] == "讲座学术" for item in data["popular_categories"])
    assert len(data["status_distribution"]) == 6
