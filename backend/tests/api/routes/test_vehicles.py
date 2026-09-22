import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Payment
from tests.utils.utils import random_student_id


def _register_and_headers(client: TestClient) -> dict[str, str]:
    reg = client.post(
        f"{settings.API_V1_STR}/kiosk/register",
        json={
            "student_id": random_student_id(),
            "first_name": "Con",
            "last_name": "Vehiculo",
        },
    )
    return {"Authorization": f"Bearer {reg.json()['token']['access_token']}"}


def test_delete_vehicle_with_payment_history_does_not_fail(
    client: TestClient, db: Session
) -> None:
    """Regresión: borrar un vehículo con pagos asociados fallaba con un
    error de integridad referencial porque la FK payment.vehicle_id no
    tenía ondelete configurado."""
    headers = _register_and_headers(client)

    vehicle_type = client.get(f"{settings.API_V1_STR}/vehicles/types").json()[0]
    vehicle = client.post(
        f"{settings.API_V1_STR}/vehicles/",
        headers=headers,
        json={"plate": "DEL123", "type_id": vehicle_type["id"]},
    )
    vehicle_id = vehicle.json()["id"]

    method_id = client.get(f"{settings.API_V1_STR}/payments/methods").json()[0]["id"]
    payment = client.post(
        f"{settings.API_V1_STR}/payments/",
        headers=headers,
        json={
            "concept": "daily_fee",
            "vehicle_id": vehicle_id,
            "method_id": method_id,
        },
    )
    assert payment.status_code == 200
    payment_id = payment.json()["id"]

    delete = client.delete(
        f"{settings.API_V1_STR}/vehicles/{vehicle_id}", headers=headers
    )
    assert delete.status_code == 200
    assert delete.json()["deleted"] is True

    # el pago sigue existiendo (auditoría), solo se desvincula del vehículo.
    db_payment = db.exec(
        select(Payment).where(Payment.id == uuid.UUID(payment_id))
    ).first()
    assert db_payment is not None
    assert db_payment.vehicle_id is None


def test_delete_other_users_vehicle_is_not_found(client: TestClient) -> None:
    owner_headers = _register_and_headers(client)
    vehicle_type = client.get(f"{settings.API_V1_STR}/vehicles/types").json()[0]
    vehicle = client.post(
        f"{settings.API_V1_STR}/vehicles/",
        headers=owner_headers,
        json={"plate": "OTR456", "type_id": vehicle_type["id"]},
    )
    vehicle_id = vehicle.json()["id"]

    other_headers = _register_and_headers(client)
    r = client.delete(
        f"{settings.API_V1_STR}/vehicles/{vehicle_id}", headers=other_headers
    )
    assert r.status_code == 404
