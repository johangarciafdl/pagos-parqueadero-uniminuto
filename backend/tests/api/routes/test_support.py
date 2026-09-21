from fastapi.testclient import TestClient

from app.core.config import settings


def test_create_and_list_my_ticket(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/support/",
        headers=normal_user_token_headers,
        json={"subject": "Pago rechazado", "message": "El pago no se refleja"},
    )
    assert r.status_code == 200
    case_number = r.json()["case_number"]
    assert r.json()["admin_reply"] is None

    mine = client.get(
        f"{settings.API_V1_STR}/support/", headers=normal_user_token_headers
    )
    assert mine.status_code == 200
    assert any(t["case_number"] == case_number for t in mine.json()["data"])


def test_list_all_tickets_requires_superuser(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/support/all")
    assert r.status_code == 401


def test_admin_can_reply_ticket_and_user_sees_the_reply(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    created = client.post(
        f"{settings.API_V1_STR}/support/",
        headers=normal_user_token_headers,
        json={"subject": "Duda sobre el plan", "message": "¿Cuándo se activa?"},
    )
    ticket_id = created.json()["id"]

    all_tickets = client.get(
        f"{settings.API_V1_STR}/support/all", headers=superuser_token_headers
    )
    assert all_tickets.status_code == 200
    assert any(t["id"] == ticket_id for t in all_tickets.json()["data"])

    reply = client.patch(
        f"{settings.API_V1_STR}/support/{ticket_id}/reply",
        headers=superuser_token_headers,
        json={"admin_reply": "Se activa apenas confirmamos el pago."},
    )
    assert reply.status_code == 200
    assert reply.json()["status"] == "resolved"
    assert reply.json()["admin_reply"] == "Se activa apenas confirmamos el pago."

    mine = client.get(
        f"{settings.API_V1_STR}/support/", headers=normal_user_token_headers
    )
    ticket = next(t for t in mine.json()["data"] if t["id"] == ticket_id)
    assert ticket["admin_reply"] == "Se activa apenas confirmamos el pago."
    assert ticket["replied_at"] is not None
