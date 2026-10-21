import pytest

from apps.activities.models import ActivityCategory, ActivityTag

pytestmark = pytest.mark.django_db


def test_admin_can_create_and_deactivate_category(admin_client, auth_client):
    payload = {
        "name": "科技前沿",
        "slug": "tech-frontier",
        "icon": "Cpu",
        "color": "#123456",
        "sort_order": 70,
    }
    forbidden = auth_client.post("/api/v1/admin/categories", payload, format="json")
    assert forbidden.status_code == 403

    created = admin_client.post("/api/v1/admin/categories", payload, format="json")
    assert created.status_code == 201, created.content
    data = created.json()["data"]
    assert data["name"] == "科技前沿"
    category_id = data["id"]

    duplicate = admin_client.post("/api/v1/admin/categories", payload, format="json")
    assert duplicate.status_code in {400, 409}

    public_list = admin_client.get("/api/v1/categories").json()["data"]
    assert any(item["slug"] == "tech-frontier" for item in public_list)

    updated = admin_client.patch(
        f"/api/v1/admin/categories/{category_id}", {"is_active": False}, format="json"
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["is_active"] is False

    public_list = admin_client.get("/api/v1/categories").json()["data"]
    assert all(item["slug"] != "tech-frontier" for item in public_list)
    admin_list = admin_client.get("/api/v1/admin/categories").json()["data"]
    assert any(
        item["id"] == category_id and item["is_active"] is False for item in admin_list
    )
    assert ActivityCategory.objects.get(pk=category_id).is_active is False


def test_admin_can_create_and_deactivate_tag(admin_client, organizer_client):
    forbidden = organizer_client.post(
        "/api/v1/admin/tags", {"name": "夜跑", "color": "#111111"}, format="json"
    )
    assert forbidden.status_code == 403

    created = admin_client.post(
        "/api/v1/admin/tags", {"name": "夜跑", "color": "#111111"}, format="json"
    )
    assert created.status_code == 201, created.content
    tag_id = created.json()["data"]["id"]

    duplicate = admin_client.post(
        "/api/v1/admin/tags", {"name": "夜跑", "color": "#222222"}, format="json"
    )
    assert duplicate.status_code in {400, 409}

    public_tags = admin_client.get("/api/v1/tags").json()["data"]
    assert any(item["id"] == tag_id for item in public_tags)

    updated = admin_client.patch(
        f"/api/v1/admin/tags/{tag_id}", {"is_active": False}, format="json"
    )
    assert updated.status_code == 200
    public_tags = admin_client.get("/api/v1/tags").json()["data"]
    assert all(item["id"] != tag_id for item in public_tags)
    assert ActivityTag.objects.get(pk=tag_id).is_active is False


def test_admin_dictionary_patch_missing_returns_404(admin_client):
    assert (
        admin_client.patch(
            "/api/v1/admin/categories/999999", {"name": "不存在"}, format="json"
        ).status_code
        == 404
    )
    assert (
        admin_client.patch(
            "/api/v1/admin/tags/999999", {"name": "不存在"}, format="json"
        ).status_code
        == 404
    )
