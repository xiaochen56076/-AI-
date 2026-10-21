import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.accounts.services import issue_tokens


def authenticated_client(user):
    client = APIClient()
    tokens = issue_tokens(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    return client


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user(db):
    user = User.objects.create_user(
        student_no="20260001",
        password="CampusHub123",
        real_name="林晓",
        nickname="小林",
        college="计算机学院",
    )
    user.roles.add(Role.objects.get(code="STUDENT"))
    return user


@pytest.fixture
def organizer_user(db):
    user = User.objects.create_user(
        student_no="T2026001",
        password="CampusHub123",
        real_name="陈老师",
        college="团委",
    )
    user.roles.add(Role.objects.get(code="ORGANIZER"))
    return user


@pytest.fixture
def another_organizer_user(db):
    user = User.objects.create_user(
        student_no="T2026002",
        password="CampusHub123",
        real_name="许老师",
        college="艺术学院",
    )
    user.roles.add(Role.objects.get(code="ORGANIZER"))
    return user


@pytest.fixture
def auditor_user(db):
    user = User.objects.create_user(
        student_no="A2026001",
        password="CampusHub123",
        real_name="赵审核",
    )
    user.roles.add(Role.objects.get(code="AUDITOR"))
    return user


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        student_no="ADMIN001",
        password="CampusHub123",
        real_name="系统管理员",
        is_staff=True,
    )
    user.roles.add(Role.objects.get(code="ADMIN"))
    return user


@pytest.fixture
def auth_client(student_user):
    return authenticated_client(student_user)


@pytest.fixture
def organizer_client(organizer_user):
    return authenticated_client(organizer_user)


@pytest.fixture
def another_organizer_client(another_organizer_user):
    return authenticated_client(another_organizer_user)


@pytest.fixture
def auditor_client(auditor_user):
    return authenticated_client(auditor_user)


@pytest.fixture
def admin_client(admin_user):
    return authenticated_client(admin_user)
