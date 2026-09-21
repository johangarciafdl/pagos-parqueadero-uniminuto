import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from tests.utils.utils import random_email, random_lower_string, random_student_id


def test_kiosk_register(client: TestClient, db: Session) -> None:
    student_id = random_student_id()
    data = {"student_id": student_id, "first_name": "Estudiante", "last_name": "de Prueba"}
    r = client.post(f"{settings.API_V1_STR}/kiosk/register", json=data)
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["student_id"] == student_id
    assert body["user"]["full_name"] == "Estudiante de Prueba"
    assert body["token"]["access_token"]
    assert body["qr_token"]

    user_db = db.exec(select(User).where(User.student_id == student_id)).first()
    assert user_db
    assert user_db.qr_token == body["qr_token"]
    assert user_db.hashed_password is None
    assert user_db.email is None


def test_kiosk_register_duplicate_student_id(client: TestClient) -> None:
    student_id = random_student_id()
    data = {"student_id": student_id, "first_name": "Uno", "last_name": "Apellido"}
    first = client.post(f"{settings.API_V1_STR}/kiosk/register", json=data)
    assert first.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/kiosk/register",
        json={"student_id": student_id, "first_name": "Otro", "last_name": "Apellido"},
    )
    assert r.status_code == 400


def test_kiosk_session_by_student_id(client: TestClient) -> None:
    student_id = random_student_id()
    reg = client.post(
        f"{settings.API_V1_STR}/kiosk/register",
        json={"student_id": student_id, "first_name": "Alguien", "last_name": "Apellido"},
    )
    assert reg.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/kiosk/session", json={"student_id": student_id}
    )
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_kiosk_session_unknown_student_id(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/kiosk/session",
        json={"student_id": "no-existe-" + random_student_id()},
    )
    assert r.status_code == 404


def test_kiosk_session_by_qr(client: TestClient) -> None:
    student_id = random_student_id()
    reg = client.post(
        f"{settings.API_V1_STR}/kiosk/register",
        json={"student_id": student_id, "first_name": "Alguien", "last_name": "Apellido"},
    )
    qr_token = reg.json()["qr_token"]

    r = client.post(f"{settings.API_V1_STR}/kiosk/qr-session", json={"qr_token": qr_token})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_kiosk_session_invalid_qr(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/kiosk/qr-session", json={"qr_token": "no-valido"}
    )
    assert r.status_code == 404


def test_kiosk_my_qr_and_regenerate(client: TestClient) -> None:
    student_id = random_student_id()
    reg = client.post(
        f"{settings.API_V1_STR}/kiosk/register",
        json={"student_id": student_id, "first_name": "Alguien", "last_name": "Apellido"},
    )
    original_qr = reg.json()["qr_token"]
    token = reg.json()["token"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    mine = client.get(f"{settings.API_V1_STR}/kiosk/my-qr", headers=headers)
    assert mine.status_code == 200
    assert mine.json()["qr_token"] == original_qr

    regenerated = client.post(
        f"{settings.API_V1_STR}/kiosk/regenerate-qr", headers=headers
    )
    assert regenerated.status_code == 200
    new_qr = regenerated.json()["qr_token"]
    assert new_qr != original_qr

    # el QR anterior ya no debe servir para iniciar sesión
    old_qr_session = client.post(
        f"{settings.API_V1_STR}/kiosk/qr-session", json={"qr_token": original_qr}
    )
    assert old_qr_session.status_code == 404


def test_register_staff_requires_superuser(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/kiosk/register-staff",
        json={
            "student_id": random_student_id(),
            "first_name": "Vigilante",
            "last_name": "Uno",
        },
    )
    assert r.status_code == 401


def test_register_staff_and_verify_qr_grants_free_access(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    student_id = random_student_id()
    reg = client.post(
        f"{settings.API_V1_STR}/kiosk/register-staff",
        headers=superuser_token_headers,
        json={"student_id": student_id, "first_name": "Vigilante", "last_name": "Dos"},
    )
    assert reg.status_code == 200
    body = reg.json()
    assert body["user"]["role"] == "EXENTO"
    qr_token = body["qr_token"]

    verify = client.post(
        f"{settings.API_V1_STR}/kiosk/verify-qr",
        headers=superuser_token_headers,
        json={"qr_token": qr_token},
    )
    assert verify.status_code == 200
    result = verify.json()
    assert result["rol"] == "EXENTO"
    assert result["documento"] == student_id
    assert result["acceso_libre"] is True


def test_verify_qr_denies_student_without_plan(client: TestClient) -> None:
    reg = client.post(
        f"{settings.API_V1_STR}/kiosk/register",
        json={
            "student_id": random_student_id(),
            "first_name": "Sin",
            "last_name": "Plan",
        },
    )
    qr_token = reg.json()["qr_token"]

    # sin superusuario no se puede usar el verificador
    unauthorized = client.post(
        f"{settings.API_V1_STR}/kiosk/verify-qr", json={"qr_token": qr_token}
    )
    assert unauthorized.status_code == 401


def test_vehicle_qr_includes_plate_and_logs_entry_exit(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    student_id = random_student_id()
    reg = client.post(
        f"{settings.API_V1_STR}/kiosk/register",
        json={"student_id": student_id, "first_name": "Con", "last_name": "Vehiculo"},
    )
    token = reg.json()["token"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    vehicle_type = client.get(f"{settings.API_V1_STR}/vehicles/types").json()[0]
    vehicle = client.post(
        f"{settings.API_V1_STR}/vehicles/",
        headers=headers,
        json={"plate": "ABC123", "type_id": vehicle_type["id"]},
    )
    assert vehicle.status_code == 200
    vehicle_id = vehicle.json()["id"]

    vqr = client.get(f"{settings.API_V1_STR}/kiosk/vehicle-qr/{vehicle_id}", headers=headers)
    assert vqr.status_code == 200
    assert vqr.json()["plate"] == "ABC123"
    qr_token = vqr.json()["qr_token"]

    entry = client.post(
        f"{settings.API_V1_STR}/kiosk/verify-qr",
        headers=superuser_token_headers,
        json={"qr_token": qr_token, "direction": "entrada"},
    )
    assert entry.status_code == 200
    assert entry.json()["placa"] == "ABC123"

    exit_ = client.post(
        f"{settings.API_V1_STR}/kiosk/verify-qr",
        headers=superuser_token_headers,
        json={"qr_token": qr_token, "direction": "salida"},
    )
    assert exit_.status_code == 200

    logs = client.get(f"{settings.API_V1_STR}/history/log", headers=headers)
    assert logs.status_code == 200
    actions = [log["action"] for log in logs.json()["data"]]
    assert "access_entry" in actions
    assert "access_exit" in actions


def test_vehicle_qr_denies_other_users_vehicle(
    client: TestClient,
) -> None:
    owner_reg = client.post(
        f"{settings.API_V1_STR}/kiosk/register",
        json={"student_id": random_student_id(), "first_name": "Dueño", "last_name": "Uno"},
    )
    owner_headers = {
        "Authorization": f"Bearer {owner_reg.json()['token']['access_token']}"
    }
    vehicle_type = client.get(f"{settings.API_V1_STR}/vehicles/types").json()[0]
    vehicle = client.post(
        f"{settings.API_V1_STR}/vehicles/",
        headers=owner_headers,
        json={"plate": "XYZ999", "type_id": vehicle_type["id"]},
    )
    vehicle_id = vehicle.json()["id"]

    other_reg = client.post(
        f"{settings.API_V1_STR}/kiosk/register",
        json={"student_id": random_student_id(), "first_name": "Otro", "last_name": "Dos"},
    )
    other_headers = {
        "Authorization": f"Bearer {other_reg.json()['token']['access_token']}"
    }

    r = client.get(
        f"{settings.API_V1_STR}/kiosk/vehicle-qr/{vehicle_id}", headers=other_headers
    )
    assert r.status_code == 404


def test_admin_created_invitado_has_no_free_access(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    created = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json={
            "email": random_email(),
            "password": random_lower_string(),
            "full_name": "Visitante de Prueba",
            "role": "INVITADO",
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["role"] == "INVITADO"

    user_db = db.exec(select(User).where(User.id == uuid.UUID(body["id"]))).first()
    assert user_db and user_db.qr_token

    verify = client.post(
        f"{settings.API_V1_STR}/kiosk/verify-qr",
        headers=superuser_token_headers,
        json={"qr_token": user_db.qr_token},
    )
    assert verify.status_code == 200
    result = verify.json()
    assert result["rol"] == "INVITADO"
    assert result["acceso_libre"] is False
