import hashlib

from fastapi.testclient import TestClient

from app.core.config import settings
from tests.utils.utils import random_student_id


def _wompi_event(
    transaction: dict, properties: list[str], secret: str, timestamp: int = 1_700_000_000
) -> dict:
    """Reconstruye un evento de Wompi con una firma válida, siguiendo el
    mismo algoritmo que `core.wompi.verify_event_signature` (concatenar los
    valores de `properties` en orden, más el timestamp y el secreto)."""
    data = {"transaction": transaction}
    parts = []
    for prop_path in properties:
        value = data
        for key in prop_path.split("."):
            value = value[key]
        parts.append(str(value))
    raw = "".join(parts) + str(timestamp) + secret
    checksum = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return {
        "event": "transaction.updated",
        "data": data,
        "timestamp": timestamp,
        "signature": {"properties": properties, "checksum": checksum},
    }


def _create_plan_purchase_payment(client: TestClient) -> tuple[dict, str]:
    student_id = random_student_id()
    reg = client.post(
        f"{settings.API_V1_STR}/kiosk/register",
        json={"student_id": student_id, "first_name": "Paga", "last_name": "Plan"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['token']['access_token']}"}

    method_id = client.get(f"{settings.API_V1_STR}/payments/methods").json()[0]["id"]
    plan_id = client.get(f"{settings.API_V1_STR}/plans/").json()["data"][0]["id"]

    payment = client.post(
        f"{settings.API_V1_STR}/payments/",
        headers=headers,
        json={"concept": "plan_purchase", "method_id": method_id, "plan_id": plan_id},
    )
    assert payment.status_code == 200
    return headers, payment.json()["wompi_reference"]


def test_webhook_rejects_invalid_signature(client: TestClient) -> None:
    _headers, reference = _create_plan_purchase_payment(client)
    event = _wompi_event(
        {"id": "1", "status": "APPROVED", "reference": reference},
        ["transaction.id", "transaction.status"],
        secret="secreto-incorrecto",
    )
    r = client.post(f"{settings.API_V1_STR}/webhooks/wompi", json=event)
    assert r.status_code == 400


def test_webhook_approves_payment_and_activates_plan(
    client: TestClient,
) -> None:
    headers, reference = _create_plan_purchase_payment(client)
    event = _wompi_event(
        {"id": "1", "status": "APPROVED", "reference": reference},
        ["transaction.id", "transaction.status"],
        secret=settings.WOMPI_EVENTS_SECRET,
    )
    r = client.post(f"{settings.API_V1_STR}/webhooks/wompi", json=event)
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

    me = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert me.json()["plan_until"] is not None

    # un segundo evento para la misma referencia ya aprobada no debe
    # reprocesarse (idempotencia) ni crear una segunda suscripción.
    replay = client.post(f"{settings.API_V1_STR}/webhooks/wompi", json=event)
    assert replay.status_code == 200
    assert replay.json().get("already_processed") is True


def test_webhook_unknown_reference_is_ignored(client: TestClient) -> None:
    event = _wompi_event(
        {"id": "1", "status": "APPROVED", "reference": "PARK-no-existe"},
        ["transaction.id", "transaction.status"],
        secret=settings.WOMPI_EVENTS_SECRET,
    )
    r = client.post(f"{settings.API_V1_STR}/webhooks/wompi", json=event)
    assert r.status_code == 200
    assert r.json()["matched"] is False
