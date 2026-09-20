from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from tests.utils.utils import random_student_id


def test_kiosk_register(client: TestClient, db: Session) -> None:
    student_id = random_student_id()
    data = {"student_id": student_id, "full_name": "Estudiante de Prueba"}
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
    data = {"student_id": student_id, "full_name": "Uno"}
    first = client.post(f"{settings.API_V1_STR}/kiosk/register", json=data)
    assert first.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/kiosk/register",
        json={"student_id": student_id, "full_name": "Otro"},
    )
    assert r.status_code == 400


def test_kiosk_session_by_student_id(client: TestClient) -> None:
    student_id = random_student_id()
    reg = client.post(
        f"{settings.API_V1_STR}/kiosk/register",
        json={"student_id": student_id, "full_name": "Alguien"},
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
        json={"student_id": student_id, "full_name": "Alguien"},
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
        json={"student_id": student_id, "full_name": "Alguien"},
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
