from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import close_old_connections
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.accounts.services import issue_tokens
from apps.activities.models import Activity, ActivityCategory
from apps.clubs.models import Club
from apps.signups.checkin import code_for_bucket, current_bucket
from apps.signups.models import CheckinRecord, Signup
from apps.signups.services import signup_for_activity
from common.exceptions import BusinessError

pytestmark = pytest.mark.django_db


def client_for(user):
    client = APIClient()
    token = issue_tokens(user)["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def make_student(number):
    user = User.objects.create_user(
        student_no=f"2026{number:04d}",
        password="CampusHub123",
        real_name=f"测试学生{number}",
        college="信息工程学院",
    )
    user.roles.add(Role.objects.get(code="STUDENT"))
    return user


@pytest.fixture
def published_activity(organizer_user):
    now = timezone.now()
    club = Club.objects.create(name="青年志愿者协会", owner=organizer_user)
    return Activity.objects.create(
        club=club,
        organizer=organizer_user,
        category=ActivityCategory.objects.get(slug="volunteer"),
        title="周末社区志愿服务",
        summary="陪伴社区老人",
        description="集合后统一前往社区。",
        location="南区校门口",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=3),
        signup_start=now - timedelta(hours=1),
        signup_end=now + timedelta(days=1),
        capacity=2,
        waitlist_enabled=True,
        waitlist_limit=3,
        checkin_mode=Activity.CheckinMode.DYNAMIC,
        status=Activity.Status.PUBLISHED,
    )


def test_signup_success_and_duplicate_is_idempotent(published_activity, auth_client):
    response = auth_client.post(
        f"/api/v1/activities/{published_activity.pk}/signup",
        {"remark": "希望参加"},
        format="json",
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == Signup.Status.SUCCESS
    assert data["remaining"] == 1
    assert Signup.objects.filter(activity=published_activity).count() == 1

    duplicate = auth_client.post(
        f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json"
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == 40002
    assert Signup.objects.filter(activity=published_activity).count() == 1

    published_activity.refresh_from_db()
    assert published_activity.signup_count == 1


def test_full_activity_enters_waitlist_with_position(published_activity):
    first, second, third = make_student(1), make_student(2), make_student(3)
    for user in (first, second):
        response = client_for(user).post(
            f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json"
        )
        assert response.status_code == 200

    third_response = client_for(third).post(
        f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json"
    )
    assert third_response.status_code == 200
    data = third_response.json()["data"]
    assert data["status"] == Signup.Status.WAITLIST
    assert data["position"] == 1

    published_activity.refresh_from_db()
    assert published_activity.signup_count == 2
    assert published_activity.waitlist_count == 1


def test_full_and_waitlist_disabled_returns_capacity_error(published_activity):
    published_activity.capacity = 1
    published_activity.waitlist_enabled = False
    published_activity.save(update_fields=["capacity", "waitlist_enabled"])

    first, second = make_student(11), make_student(12)
    assert (
        client_for(first)
        .post(f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json")
        .status_code
        == 200
    )
    full = client_for(second).post(
        f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json"
    )
    assert full.status_code == 409
    assert full.json()["code"] == 40001


def test_waitlist_limit_is_enforced(published_activity):
    published_activity.capacity = 1
    published_activity.waitlist_limit = 1
    published_activity.save(update_fields=["capacity", "waitlist_limit"])
    first, second, third = make_student(21), make_student(22), make_student(23)

    assert (
        client_for(first)
        .post(f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json")
        .status_code
        == 200
    )
    waitlisted = client_for(second).post(
        f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json"
    )
    assert waitlisted.json()["data"]["status"] == Signup.Status.WAITLIST

    rejected = client_for(third).post(
        f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json"
    )
    assert rejected.status_code == 409
    assert rejected.json()["code"] == 40001


def test_cancel_success_promotes_first_waitlist_user(published_activity):
    published_activity.capacity = 1
    published_activity.save(update_fields=["capacity"])
    first, second = make_student(31), make_student(32)
    first_client = client_for(first)
    second_client = client_for(second)

    first_signup = first_client.post(
        f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json"
    ).json()["data"]
    second_response = second_client.post(
        f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json"
    ).json()["data"]
    assert second_response["status"] == Signup.Status.WAITLIST

    cancelled = first_client.delete(f"/api/v1/activities/{published_activity.pk}/signup")
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["promoted_signup_id"] == second_response["signup_id"]

    published_activity.refresh_from_db()
    promoted = Signup.objects.get(pk=second_response["signup_id"])
    assert promoted.status == Signup.Status.SUCCESS
    assert published_activity.signup_count == 1
    assert published_activity.waitlist_count == 0
    assert first_signup["status"] == Signup.Status.SUCCESS


def test_waitlist_cancel_decrements_waitlist_count_without_promotion(published_activity):
    published_activity.capacity = 1
    published_activity.save(update_fields=["capacity"])
    first, second = make_student(41), make_student(42)
    client_for(first).post(f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json")
    waitlisted = client_for(second).post(
        f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json"
    )
    assert waitlisted.json()["data"]["status"] == Signup.Status.WAITLIST

    cancelled = client_for(second).delete(f"/api/v1/activities/{published_activity.pk}/signup")
    assert cancelled.status_code == 200
    published_activity.refresh_from_db()
    assert published_activity.waitlist_count == 0
    assert (
        Signup.objects.get(user=second, activity=published_activity).status
        == Signup.Status.CANCELLED
    )


def test_cancelled_user_can_sign_up_again_with_single_record(published_activity):
    published_activity.capacity = 1
    published_activity.waitlist_enabled = False
    published_activity.save(update_fields=["capacity", "waitlist_enabled"])
    user = make_student(51)
    client = client_for(user)
    client.post(f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json")
    client.delete(f"/api/v1/activities/{published_activity.pk}/signup")

    again = client.post(f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json")
    assert again.status_code == 200
    assert again.json()["data"]["status"] == Signup.Status.SUCCESS
    assert Signup.objects.filter(activity=published_activity, user=user).count() == 1


def test_cancel_after_deadline_is_rejected(published_activity, auth_client):
    auth_client.post(f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json")
    published_activity.signup_end = timezone.now() - timedelta(minutes=1)
    published_activity.save(update_fields=["signup_end"])

    response = auth_client.delete(f"/api/v1/activities/{published_activity.pk}/signup")
    assert response.status_code == 409
    assert response.json()["code"] == 40006


def test_my_signups_grouping(published_activity, auth_client):
    auth_client.post(f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json")
    response = auth_client.get("/api/v1/my/signups", {"group": "upcoming"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["results"][0]["activity"]["title"] == published_activity.title
    assert data["results"][0]["status"] == Signup.Status.SUCCESS


def test_organizer_can_view_roster_and_export_csv(
    published_activity, organizer_client, auth_client
):
    auth_client.post(f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json")

    forbidden = auth_client.get(f"/api/v1/activities/{published_activity.pk}/signups")
    assert forbidden.status_code == 403

    roster = organizer_client.get(f"/api/v1/activities/{published_activity.pk}/signups")
    assert roster.status_code == 200
    assert roster.json()["data"]["total"] == 1
    assert roster.json()["data"]["results"][0]["user"]["student_no"] == "20260001"

    exported = organizer_client.get(f"/api/v1/activities/{published_activity.pk}/signups/export")
    assert exported.status_code == 200
    assert "attachment" in exported["Content-Disposition"]
    content = exported.content.decode("utf-8-sig")
    assert "学号,姓名,学院" in content
    assert "20260001" in content


def test_cancelling_activity_cancels_registrations(
    published_activity, organizer_client, auth_client
):
    auth_client.post(f"/api/v1/activities/{published_activity.pk}/signup", {}, format="json")
    cancelled = organizer_client.post(
        f"/api/v1/activities/{published_activity.pk}/cancel",
        {"reason": "场地不可用"},
        format="json",
    )
    assert cancelled.status_code == 200
    published_activity.refresh_from_db()
    assert published_activity.signup_count == 0
    signup = Signup.objects.get(activity=published_activity)
    assert signup.status == Signup.Status.CANCELLED


@pytest.mark.django_db(transaction=True)
def test_concurrent_signup_never_oversells(organizer_user):
    now = timezone.now()
    club = Club.objects.create(name="并发测试社团", owner=organizer_user)
    activity = Activity.objects.create(
        club=club,
        organizer=organizer_user,
        category=ActivityCategory.objects.get(slug="lecture"),
        title="只有十个座位的讲座",
        summary="并发报名测试",
        location="报告厅",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=2),
        signup_start=now - timedelta(hours=1),
        signup_end=now + timedelta(days=1),
        capacity=10,
        waitlist_enabled=False,
        status=Activity.Status.PUBLISHED,
    )
    users = User.objects.bulk_create(
        [
            User(
                student_no=f"2027{index:04d}",
                real_name=f"并发学生{index}",
                password="!",
            )
            for index in range(100)
        ]
    )
    barrier = Barrier(100)

    def attempt(user):
        close_old_connections()
        try:
            barrier.wait(timeout=20)
            signup_for_activity(activity.pk, user)
            return "success"
        except BusinessError as exc:
            return f"error:{exc.biz_code}"
        except Exception as exc:  # pragma: no cover - surfaced in assertion message
            return f"unexpected:{type(exc).__name__}:{exc}"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=100) as pool:
        results = list(pool.map(attempt, users))

    activity.refresh_from_db()
    success_count = Signup.objects.filter(activity=activity, status=Signup.Status.SUCCESS).count()
    assert results.count("success") == 10, results
    assert success_count == 10
    assert activity.signup_count == 10
    assert Signup.objects.filter(activity=activity).count() == 10
    assert all(item == "success" or item == "error:40001" for item in results)


def make_checkin_activity(organizer, **overrides):
    now = timezone.now()
    values = {
        "club": Club.objects.create(name="签到测试社团", owner=organizer),
        "organizer": organizer,
        "category": ActivityCategory.objects.get(slug="lecture"),
        "title": "人工智能前沿讲座",
        "summary": "签到功能测试",
        "location": "图书馆报告厅",
        "start_time": now + timedelta(minutes=10),
        "end_time": now + timedelta(hours=3),
        "signup_start": now - timedelta(hours=1),
        "signup_end": now + timedelta(minutes=5),
        "capacity": 20,
        "waitlist_enabled": True,
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


def fetch_checkin_code(organizer_client, activity):
    response = organizer_client.post(f"/api/v1/activities/{activity.pk}/checkin-code")
    assert response.status_code == 200, response.content
    return response.json()["data"]


def scan(client, activity, code):
    return client.post(
        "/api/v1/checkin",
        {"activity_id": activity.pk, "code": code},
        format="json",
    )


def test_dynamic_code_and_scan_checkin_success(
    organizer_user, organizer_client, auth_client
):
    activity = make_checkin_activity(organizer_user)
    sign_up(auth_client, activity)

    code_data = fetch_checkin_code(organizer_client, activity)
    assert len(code_data["code"]) == 8
    assert code_data["expires_at"]
    assert code_data["qr_content"].startswith("campushub://checkin?")
    assert code_data["checked_in_count"] == 0

    response = scan(auth_client, activity, code_data["code"])
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["checkin_method"] == CheckinRecord.Method.SCAN
    assert data["checked_in_count"] == 1
    assert data["student_no"] == "20260001"

    signup = Signup.objects.get(activity=activity, user__student_no="20260001")
    assert signup.status == Signup.Status.CHECKED_IN
    record = CheckinRecord.objects.get(signup=signup)
    assert record.activity_id == activity.pk
    assert record.method == CheckinRecord.Method.SCAN

    roster = organizer_client.get(f"/api/v1/activities/{activity.pk}/signups").json()["data"]
    assert roster["results"][0]["checked_in_at"]
    assert roster["results"][0]["checkin_method_text"] == "扫码签到"

    detail = auth_client.get(f"/api/v1/activities/{activity.pk}").json()["data"]
    assert detail["checked_in_count"] == 1
    assert detail["my_signup"]["checked_in"] is True

    mine = auth_client.get("/api/v1/my/signups", {"group": "attended"}).json()["data"]
    assert mine["results"][0]["checked_in_at"]
    assert mine["results"][0]["checkin_method_text"] == "扫码签到"


def test_checkin_rejects_tampered_and_expired_codes(
    organizer_user, organizer_client, auth_client
):
    activity = make_checkin_activity(organizer_user)
    sign_up(auth_client, activity)
    code = fetch_checkin_code(organizer_client, activity)["code"]

    tampered = code[:-1] + ("0" if code[-1] != "0" else "1")
    response = scan(auth_client, activity, tampered)
    assert response.status_code == 409
    assert response.json()["code"] == 40011

    expired = code_for_bucket(activity, current_bucket() - 20)
    response = scan(auth_client, activity, expired)
    assert response.status_code == 409
    assert response.json()["code"] == 40011
    assert not CheckinRecord.objects.filter(activity=activity).exists()


def test_checkin_requires_successful_signup(auth_client, organizer_user, organizer_client):
    activity = make_checkin_activity(organizer_user)
    code = fetch_checkin_code(organizer_client, activity)["code"]

    response = scan(auth_client, activity, code)
    assert response.status_code == 409
    assert response.json()["code"] == 40012


def test_duplicate_checkin_is_rejected(organizer_user, organizer_client, auth_client):
    activity = make_checkin_activity(organizer_user)
    sign_up(auth_client, activity)
    code = fetch_checkin_code(organizer_client, activity)["code"]

    assert scan(auth_client, activity, code).status_code == 200
    duplicate = scan(auth_client, activity, code)
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == 40003
    assert CheckinRecord.objects.filter(activity=activity).count() == 1


def test_checkin_is_rejected_outside_time_window(
    published_activity, organizer_client, auth_client
):
    sign_up(auth_client, published_activity)
    code = fetch_checkin_code(organizer_client, published_activity)["code"]

    response = scan(auth_client, published_activity, code)
    assert response.status_code == 409
    assert response.json()["code"] == 40010


def test_static_checkin_mode_has_no_expiry(organizer_user, organizer_client, auth_client):
    activity = make_checkin_activity(
        organizer_user, checkin_mode=Activity.CheckinMode.STATIC
    )
    sign_up(auth_client, activity)
    code_data = fetch_checkin_code(organizer_client, activity)
    assert code_data["expires_at"] is None
    assert scan(auth_client, activity, code_data["code"]).status_code == 200


def test_organizer_manual_checkin_records_audit_fields(
    organizer_user, organizer_client, auth_client
):
    activity = make_checkin_activity(organizer_user)
    sign_up(auth_client, activity)

    response = organizer_client.post(
        f"/api/v1/activities/{activity.pk}/checkin-manual",
        {"student_no": "20260001", "reason": "学生手机没电，现场核验学生证"},
        format="json",
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["checkin_method"] == CheckinRecord.Method.MANUAL
    assert data["real_name"] == "林晓"

    record = CheckinRecord.objects.get(activity=activity)
    assert record.method == CheckinRecord.Method.MANUAL
    assert record.operator_id == organizer_user.pk
    assert "学生证" in record.reason
    assert Signup.objects.get(activity=activity).status == Signup.Status.CHECKED_IN

    duplicate = organizer_client.post(
        f"/api/v1/activities/{activity.pk}/checkin-manual",
        {"student_no": "20260001", "reason": "重复补签测试"},
        format="json",
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == 40003


def test_manual_checkin_validates_permission_reason_and_student(
    organizer_user, organizer_client, another_organizer_client, auth_client
):
    activity = make_checkin_activity(organizer_user)
    sign_up(auth_client, activity)

    forbidden = another_organizer_client.post(
        f"/api/v1/activities/{activity.pk}/checkin-manual",
        {"student_no": "20260001", "reason": "越权补签"},
        format="json",
    )
    assert forbidden.status_code == 403

    student_denied = auth_client.post(
        f"/api/v1/activities/{activity.pk}/checkin-manual",
        {"student_no": "20260001", "reason": "学生不能补签"},
        format="json",
    )
    assert student_denied.status_code == 403

    short_reason = organizer_client.post(
        f"/api/v1/activities/{activity.pk}/checkin-manual",
        {"student_no": "20260001", "reason": "x"},
        format="json",
    )
    assert short_reason.status_code == 400

    missing_student = organizer_client.post(
        f"/api/v1/activities/{activity.pk}/checkin-manual",
        {"student_no": "20990000", "reason": "现场核验"},
        format="json",
    )
    assert missing_student.status_code == 404
    assert missing_student.json()["code"] == 40015


def test_only_owner_can_generate_checkin_code(
    organizer_user, another_organizer_client, auth_client
):
    activity = make_checkin_activity(organizer_user)

    assert (
        auth_client.post(f"/api/v1/activities/{activity.pk}/checkin-code").status_code
        == 403
    )
    assert (
        another_organizer_client.post(
            f"/api/v1/activities/{activity.pk}/checkin-code"
        ).status_code
        == 403
    )
