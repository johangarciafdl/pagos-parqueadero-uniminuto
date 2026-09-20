from fastapi.testclient import TestClient

from app.core.config import settings


def test_list_plans_hides_inactive(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/plans/")
    assert r.status_code == 200
    assert all(plan["active"] for plan in r.json()["data"])


def test_list_all_plans_requires_superuser(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/plans/all")
    assert r.status_code == 401


def test_admin_can_activate_and_deactivate_plan(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    all_plans = client.get(
        f"{settings.API_V1_STR}/plans/all", headers=superuser_token_headers
    )
    assert all_plans.status_code == 200
    plan = all_plans.json()["data"][0]
    assert plan["active"] is False

    activated = client.patch(
        f"{settings.API_V1_STR}/plans/{plan['id']}",
        headers=superuser_token_headers,
        json={"active": True},
    )
    assert activated.status_code == 200
    assert activated.json()["active"] is True

    visible = client.get(f"{settings.API_V1_STR}/plans/")
    assert any(p["id"] == plan["id"] for p in visible.json()["data"])

    deactivated = client.patch(
        f"{settings.API_V1_STR}/plans/{plan['id']}",
        headers=superuser_token_headers,
        json={"active": False},
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["active"] is False
