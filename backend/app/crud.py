import uuid
from typing import Any

from sqlmodel import Session, select

from app.core.qr import create_qr_token, decode_qr_token
from app.core.security import get_password_hash, verify_password
from app.models import (
    GuestRegister,
    KioskRegister,
    StaffRegister,
    User,
    UserCreate,
    UserRole,
    UserUpdate,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    db_obj.qr_token = create_qr_token(db_obj)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def create_kiosk_user(*, session: Session, data: KioskRegister) -> User:
    db_obj = User(
        student_id=data.student_id,
        first_name=data.first_name,
        last_name=data.last_name,
        full_name=f"{data.first_name} {data.last_name}",
        role=UserRole.ESTUDIANTE,
    )
    db_obj.qr_token = create_qr_token(db_obj)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def create_staff_user(*, session: Session, data: StaffRegister) -> User:
    """Alta de personal exento de pago (solo la crea un admin)."""
    db_obj = User(
        student_id=data.student_id,
        first_name=data.first_name,
        last_name=data.last_name,
        full_name=f"{data.first_name} {data.last_name}",
        role=UserRole.EXENTO,
    )
    db_obj.qr_token = create_qr_token(db_obj)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def create_guest_user(*, session: Session, data: GuestRegister) -> User:
    """Alta de un invitado/visitante: se identifica con documento nacional
    en vez de un carné de estudiante, paga la misma tarifa que un
    estudiante."""
    db_obj = User(
        student_id=data.document_number,
        document_type=data.document_type,
        first_name=data.first_name,
        last_name=data.last_name,
        full_name=f"{data.first_name} {data.last_name}",
        role=UserRole.INVITADO,
    )
    db_obj.qr_token = create_qr_token(db_obj)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def regenerate_qr_token(*, session: Session, user: User) -> User:
    user.qr_token = create_qr_token(user)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def reissue_qr_token(*, session: Session, user: User) -> User:
    """Reemite el QR con el estado actual (ej. tras aprobar un plan), sin
    que el usuario lo pida — para que el QR "cambie" cuando cambia su
    condición de pago."""
    return regenerate_qr_token(session=session, user=user)


_QR_RELEVANT_FIELDS = {"first_name", "last_name", "full_name", "student_id", "role"}


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    if db_user.qr_token and _QR_RELEVANT_FIELDS & user_data.keys():
        db_user.qr_token = create_qr_token(db_user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_user_by_student_id(*, session: Session, student_id: str) -> User | None:
    statement = select(User).where(User.student_id == student_id)
    return session.exec(statement).first()


def get_user_by_qr_token(*, session: Session, qr_token: str) -> User | None:
    """Decodifica el JWT del QR y confirma que sigue siendo el vigente para
    ese usuario (si se regeneró después de emitirse, este ya no sirve)."""
    payload = decode_qr_token(qr_token)
    if not payload or not payload["sub"]:
        return None
    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        return None
    user = session.get(User, user_id)
    if not user or user.qr_token != qr_token:
        return None
    return user


# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user or db_user.hashed_password is None:
        # Prevent timing attacks by running password verification even when user doesn't exist
        # This ensures the response time is similar whether or not the email exists
        verify_password(password, DUMMY_HASH)
        return None
    verified, updated_password_hash = verify_password(password, db_user.hashed_password)
    if not verified:
        return None
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user
