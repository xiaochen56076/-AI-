import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, User

pytestmark = pytest.mark.django_db


def register_payload(**overrides):
    payload = {
        "student_no": "20261234",
        "password": "CampusHub123",
        "confirm_password": "CampusHub123",
        "real_name": "周可",
        "nickname": "可可",
        "college": "外国语学院",
        "major": "英语",
        "grade": 2026,
    }
    payload.update(overrides)
    return payload


def test_register_creates_student_and_tokens(api_client):
    response = api_client.post("/api/v1/auth/register", register_payload(), format="json")

    assert response.status_code == 201
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["user"]["student_no"] == "20261234"
    assert body["data"]["user"]["roles"][0]["code"] == "STUDENT"
    assert body["data"]["access"]
    assert body["data"]["refresh"]
    user = User.objects.get(student_no="20261234")
    assert user.check_password("CampusHub123")
    assert user.password.startswith(("bcrypt", "md5"))


def test_register_rejects_duplicate_and_mismatched_password(api_client, student_user):
    duplicate = api_client.post(
        "/api/v1/auth/register", register_payload(student_no=student_user.student_no), format="json"
    )
    assert duplicate.status_code == 400
    assert duplicate.json()["code"] == 10001

    mismatch = api_client.post(
        "/api/v1/auth/register", register_payload(confirm_password="Different123"), format="json"
    )
    assert mismatch.status_code == 400
    assert "两次输入的密码不一致" in mismatch.json()["message"]


def test_login_and_me(api_client, student_user):
    login = api_client.post(
        "/api/v1/auth/login",
        {"student_no": student_user.student_no, "password": "CampusHub123"},
        format="json",
    )
    assert login.status_code == 200
    data = login.json()["data"]
    assert data["user"]["display_name"] == "小林"
    assert set(data["user"]["permissions"]) == set()

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")
    me = client.get("/api/v1/users/me")
    assert me.status_code == 200
    assert me.json()["data"]["student_no"] == student_user.student_no


def test_login_wrong_password_is_rejected(api_client, student_user):
    response = api_client.post(
        "/api/v1/auth/login",
        {"student_no": student_user.student_no, "password": "wrong-password"},
        format="json",
    )
    assert response.status_code == 401
    assert response.json()["code"] == 20001


def test_refresh_token_rotation(api_client, student_user):
    login = api_client.post(
        "/api/v1/auth/login",
        {"student_no": student_user.student_no, "password": "CampusHub123"},
        format="json",
    ).json()
    response = api_client.post(
        "/api/v1/auth/refresh", {"refresh": login["data"]["refresh"]}, format="json"
    )
    assert response.status_code == 200
    assert response.json()["data"]["access"]
    assert response.json()["data"]["refresh"] != login["data"]["refresh"]


def test_logout_blacklists_access_and_refresh(api_client, student_user):
    login = api_client.post(
        "/api/v1/auth/login",
        {"student_no": student_user.student_no, "password": "CampusHub123"},
        format="json",
    ).json()["data"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login['access']}")

    logout = api_client.post("/api/v1/auth/logout", {"refresh": login["refresh"]}, format="json")
    assert logout.status_code == 200

    me = api_client.get("/api/v1/users/me")
    assert me.status_code == 401

    refresh = APIClient().post("/api/v1/auth/refresh", {"refresh": login["refresh"]}, format="json")
    assert refresh.status_code == 401


def test_profile_update(auth_client):
    response = auth_client.patch(
        "/api/v1/users/me",
        {"nickname": "新昵称", "college": "软件学院"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["data"]["nickname"] == "新昵称"
    assert response.json()["data"]["college"] == "软件学院"


def test_student_cannot_manage_users(api_client, student_user):
    from apps.accounts.services import issue_tokens

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(student_user)['access']}")
    response = api_client.get("/api/v1/admin/users")
    assert response.status_code == 403
    assert response.json()["code"] == 20003


def test_admin_can_filter_and_update_users(api_client, admin_user, student_user):
    from apps.accounts.services import issue_tokens

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(admin_user)['access']}")
    listing = api_client.get("/api/v1/admin/users", {"keyword": "20260001"})
    assert listing.status_code == 200
    assert listing.json()["data"]["total"] == 1

    update = api_client.patch(
        f"/api/v1/admin/users/{student_user.pk}",
        {"roles": ["STUDENT", "ORGANIZER"], "status": 0},
        format="json",
    )
    assert update.status_code == 200
    assert {role["code"] for role in update.json()["data"]["roles"]} == {"STUDENT", "ORGANIZER"}


def test_admin_cannot_disable_self(api_client, admin_user):
    from apps.accounts.services import issue_tokens

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(admin_user)['access']}")
    response = api_client.patch(
        f"/api/v1/admin/users/{admin_user.pk}",
        {"status": 1},
        format="json",
    )
    assert response.status_code == 400
    assert "不能禁用当前登录账号" in response.json()["message"]


def test_disabled_user_cannot_login(api_client, student_user):
    student_user.status = User.Status.DISABLED
    student_user.save(update_fields=["status"])
    response = api_client.post(
        "/api/v1/auth/login",
        {"student_no": student_user.student_no, "password": "CampusHub123"},
        format="json",
    )
    assert response.status_code == 401


def test_change_password(auth_client):
    response = auth_client.post(
        "/api/v1/users/me/password",
        {
            "old_password": "CampusHub123",
            "new_password": "NewCampus456",
            "confirm_password": "NewCampus456",
        },
        format="json",
    )
    assert response.status_code == 200


def test_rbac_roles_have_expected_permissions():
    assert set(
        Role.objects.get(code="ORGANIZER").permissions.values_list("codename", flat=True)
    ) >= {
        "activity:create",
        "activity:manage",
        "checkin:manage",
    }
    assert set(Role.objects.get(code="AUDITOR").permissions.values_list("codename", flat=True)) == {
        "activity:audit"
    }
