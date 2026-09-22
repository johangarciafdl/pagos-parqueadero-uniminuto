from fastapi.testclient import TestClient

from app.core.config import settings
from tests.utils.utils import random_student_id


def test_register_guest_creates_invitado_with_document(client: TestClient) -> None:
    document_number = random_student_id()
    r = client.post(
        f"{settings.API_V1_STR}/kiosk/register-guest",
        json={
            "document_type": "CC",
            "document_number": document_number,
            "first_name": "Visitante",
            "last_name": "De Prueba",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["role"] == "INVITADO"
    assert body["user"]["student_id"] == document_number
    assert body["user"]["document_type"] == "CC"
    assert body["token"]["access_token"]
    assert body["qr_token"]


def test_register_guest_duplicate_document_fails(client: TestClient) -> None:
    document_number = random_student_id()
    data = {
        "document_type": "CE",
        "document_number": document_number,
        "first_name": "Uno",
        "last_name": "Apellido",
    }
    first = client.post(f"{settings.API_V1_STR}/kiosk/register-guest", json=data)
    assert first.status_code == 200

    second = client.post(f"{settings.API_V1_STR}/kiosk/register-guest", json=data)
    assert second.status_code == 400


def test_guest_can_reenter_with_document_number(client: TestClient) -> None:
    document_number = random_student_id()
    client.post(
        f"{settings.API_V1_STR}/kiosk/register-guest",
        json={
            "document_type": "TI",
            "document_number": document_number,
            "first_name": "Otro",
            "last_name": "Invitado",
        },
    )
    r = client.post(
        f"{settings.API_V1_STR}/kiosk/session", json={"student_id": document_number}
    )
    assert r.status_code == 200
    assert r.json()["access_token"]
