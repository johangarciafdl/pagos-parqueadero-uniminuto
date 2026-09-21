from fastapi.testclient import TestClient

from app.core.config import settings


def test_list_plans_shows_the_monthly_plan_by_default(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/plans/")
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 1
    assert all(plan["active"] for plan in r.json()["data"])


def test_list_all_plans_requires_superuser(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/plans/all")
    assert r.status_code == 401


def test_admin_can_deactivate_and_reactivate_plan(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    all_plans = client.get(
        f"{settings.API_V1_STR}/plans/all", headers=superuser_token_headers
    )
    assert all_plans.status_code == 200
    plan = all_plans.json()["data"][0]
    assert plan["active"] is True

    deactivated = client.patch(
        f"{settings.API_V1_STR}/plans/{plan['id']}",
        headers=superuser_token_headers,
        json={"active": False},
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["active"] is False

    hidden = client.get(f"{settings.API_V1_STR}/plans/")
    assert all(p["id"] != plan["id"] for p in hidden.json()["data"])

    reactivated = client.patch(
        f"{settings.API_V1_STR}/plans/{plan['id']}",
        headers=superuser_token_headers,
        json={"active": True},
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["active"] is True
