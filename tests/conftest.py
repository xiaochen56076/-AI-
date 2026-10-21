import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, User


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
def auth_client(api_client, student_user):
    from apps.accounts.services import issue_tokens

    tokens = issue_tokens(student_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    return api_client


@pytest.fixture
def organizer_client(api_client, organizer_user):
    from apps.accounts.services import issue_tokens

    tokens = issue_tokens(organizer_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    return api_client
