from datetime import timedelta

import pytest
from django.utils import timezone

from apps.activities.models import Activity, ActivityCategory, AuditRecord, Favorite

pytestmark = pytest.mark.django_db


def activity_payload(**overrides):
    now = timezone.now()
    start = now + timedelta(days=3)
    payload = {
        "title": "秋季校园公益跑",
        "summary": "用脚步为乡村孩子募集图书",
        "description": "环湖五公里公益跑，完赛可获得志愿时长。",
        "location": "东校区湖畔广场",
        "start_time": (start).isoformat(),
        "end_time": (start + timedelta(hours=3)).isoformat(),
        "signup_start": (now - timedelta(hours=1)).isoformat(),
        "signup_end": (start - timedelta(hours=2)).isoformat(),
        "capacity": 100,
        "waitlist_enabled": True,
        "waitlist_limit": 20,
        "checkin_mode": 2,
        "category_id": ActivityCategory.objects.get(slug="volunteer").id,
    }
    payload.update(overrides)
    return payload


def create_draft(client, **overrides):
    return client.post("/api/v1/activities", activity_payload(**overrides), format="json")


def test_organizer_creates_draft_with_default_club(organizer_client):
    response = create_draft(organizer_client)

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["status"] == Activity.Status.DRAFT
    assert data["club"]["name"] == "陈老师的活动社"
    assert data["checkin_secret"]
    assert data["can_manage"] is True


def test_student_cannot_create_activity(auth_client):
    response = create_draft(auth_client)
    assert response.status_code == 403
    assert response.json()["code"] == 20003


def test_activity_time_validation(organizer_client):
    now = timezone.now()
    response = create_draft(
        organizer_client,
        end_time=(now + timedelta(days=2)).isoformat(),
        start_time=(now + timedelta(days=3)).isoformat(),
    )
    assert response.status_code == 400
    assert "结束时间必须晚于开始时间" in response.json()["message"]


def test_submit_and_approve_activity(organizer_client, auditor_client):
    activity_id = create_draft(organizer_client).json()["data"]["id"]

    submitted = organizer_client.post(f"/api/v1/activities/{activity_id}/submit")
    assert submitted.status_code == 200
    assert submitted.json()["data"]["status"] == Activity.Status.PENDING

    hidden = organizer_client.get(f"/api/v1/activities/{activity_id}")
    assert hidden.status_code == 200

    public = auditor_client.get(f"/api/v1/activities/{activity_id}")
    assert public.status_code == 200

    queue = auditor_client.get("/api/v1/admin/audits")
    assert queue.status_code == 200
    assert queue.json()["data"]["total"] == 1

    approved = auditor_client.post(
        f"/api/v1/admin/audits/{activity_id}",
        {"action": 1, "comment": "内容合规，通过"},
        format="json",
    )
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == Activity.Status.PUBLISHED
    assert AuditRecord.objects.filter(activity_id=activity_id, action=1).exists()

    from rest_framework.test import APIClient

    listing = APIClient().get("/api/v1/activities")
    assert listing.json()["data"]["total"] == 1
    assert listing.json()["data"]["results"][0]["title"] == "秋季校园公益跑"


def test_reject_requires_comment_and_allows_resubmit(organizer_client, auditor_client):
    activity_id = create_draft(organizer_client).json()["data"]["id"]
    organizer_client.post(f"/api/v1/activities/{activity_id}/submit")

    rejected = auditor_client.post(
        f"/api/v1/admin/audits/{activity_id}",
        {"action": 2, "comment": ""},
        format="json",
    )
    assert rejected.status_code == 400
    assert "必须填写审核意见" in rejected.json()["message"]

    rejected = auditor_client.post(
        f"/api/v1/admin/audits/{activity_id}",
        {"action": 2, "comment": "活动描述需要补充安全预案"},
        format="json",
    )
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == Activity.Status.REJECTED

    resubmitted = organizer_client.post(f"/api/v1/activities/{activity_id}/submit")
    assert resubmitted.status_code == 200
    assert resubmitted.json()["data"]["status"] == Activity.Status.PENDING


def test_student_cannot_access_audit_console(auth_client):
    response = auth_client.get("/api/v1/admin/audits")
    assert response.status_code == 403


def test_non_owner_cannot_edit(organizer_client, another_organizer_client):
    activity_id = create_draft(organizer_client).json()["data"]["id"]
    response = another_organizer_client.patch(
        f"/api/v1/activities/{activity_id}",
        {"summary": "恶意修改"},
        format="json",
    )
    assert response.status_code == 403


def test_draft_can_be_edited_then_published_fields_are_restricted(organizer_client, auditor_client):
    activity_id = create_draft(organizer_client).json()["data"]["id"]
    update = organizer_client.patch(
        f"/api/v1/activities/{activity_id}",
        {"title": "公益跑（ updated ）", "capacity": 120},
        format="json",
    )
    assert update.status_code == 200
    assert update.json()["data"]["capacity"] == 120

    organizer_client.post(f"/api/v1/activities/{activity_id}/submit")
    auditor_client.post(f"/api/v1/admin/audits/{activity_id}", {"action": 1}, format="json")

    forbidden = organizer_client.patch(
        f"/api/v1/activities/{activity_id}",
        {"capacity": 999},
        format="json",
    )
    assert forbidden.status_code == 409
    assert "只能修改简介" in forbidden.json()["message"]

    allowed = organizer_client.patch(
        f"/api/v1/activities/{activity_id}",
        {"summary": "更新后的简介"},
        format="json",
    )
    assert allowed.status_code == 200
    assert allowed.json()["data"]["summary"] == "更新后的简介"


def test_public_list_filters_search_and_sort(organizer_client, auditor_client):
    first_id = create_draft(
        organizer_client,
        title="人工智能前沿讲座",
        category_id=ActivityCategory.objects.get(slug="lecture").id,
    ).json()["data"]["id"]
    second_id = create_draft(
        organizer_client,
        title="篮球联赛",
        category_id=ActivityCategory.objects.get(slug="sports").id,
    ).json()["data"]["id"]
    for activity_id in (first_id, second_id):
        organizer_client.post(f"/api/v1/activities/{activity_id}/submit")
        auditor_client.post(f"/api/v1/admin/audits/{activity_id}", {"action": 1}, format="json")

    from rest_framework.test import APIClient

    client = APIClient()
    by_keyword = client.get("/api/v1/activities", {"keyword": "篮球"})
    assert by_keyword.json()["data"]["total"] == 1
    assert by_keyword.json()["data"]["results"][0]["id"] == second_id

    by_category = client.get("/api/v1/activities", {"category": "lecture"})
    assert by_category.json()["data"]["total"] == 1
    assert by_category.json()["data"]["results"][0]["id"] == first_id

    hot = client.get("/api/v1/activities", {"sort": "hot"})
    assert hot.status_code == 200


def test_detail_increments_views_and_favorite_toggle(organizer_client, auditor_client, auth_client):
    activity_id = create_draft(organizer_client).json()["data"]["id"]
    organizer_client.post(f"/api/v1/activities/{activity_id}/submit")
    auditor_client.post(f"/api/v1/admin/audits/{activity_id}", {"action": 1}, format="json")

    detail = auth_client.get(f"/api/v1/activities/{activity_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["view_count"] == 1

    favorite = auth_client.post(f"/api/v1/activities/{activity_id}/favorite")
    assert favorite.status_code == 200
    assert favorite.json()["data"]["is_favorited"] is True
    assert Favorite.objects.filter(activity_id=activity_id).count() == 1

    again = auth_client.post(f"/api/v1/activities/{activity_id}/favorite")
    assert again.status_code == 200
    assert Favorite.objects.filter(activity_id=activity_id).count() == 1

    favorites = auth_client.get("/api/v1/my/favorites")
    assert favorites.json()["data"]["total"] == 1

    unfavorite = auth_client.delete(f"/api/v1/activities/{activity_id}/favorite")
    assert unfavorite.status_code == 200
    assert not Favorite.objects.filter(activity_id=activity_id).exists()


def test_draft_detail_hidden_from_public(organizer_client):
    activity_id = create_draft(organizer_client).json()["data"]["id"]

    from rest_framework.test import APIClient

    public = APIClient().get(f"/api/v1/activities/{activity_id}")
    assert public.status_code == 404

    owner = organizer_client.get(f"/api/v1/activities/{activity_id}")
    assert owner.status_code == 200


def test_cancel_published_activity_requires_reason(organizer_client, auditor_client):
    activity_id = create_draft(organizer_client).json()["data"]["id"]
    organizer_client.post(f"/api/v1/activities/{activity_id}/submit")
    auditor_client.post(f"/api/v1/admin/audits/{activity_id}", {"action": 1}, format="json")

    no_reason = organizer_client.post(f"/api/v1/activities/{activity_id}/cancel", {}, format="json")
    assert no_reason.status_code == 400

    cancelled = organizer_client.post(
        f"/api/v1/activities/{activity_id}/cancel",
        {"reason": "场地临时调整"},
        format="json",
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == Activity.Status.CANCELLED

    from rest_framework.test import APIClient

    listing = APIClient().get("/api/v1/activities")
    assert listing.json()["data"]["total"] == 0


def test_categories_and_tags_are_public(api_client):
    categories = api_client.get("/api/v1/categories")
    tags = api_client.get("/api/v1/tags")
    assert categories.status_code == 200
    assert len(categories.json()["data"]) == 6
    assert tags.status_code == 200
    assert any(item["name"] == "志愿时长" for item in tags.json()["data"])
