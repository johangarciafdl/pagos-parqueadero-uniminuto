from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import (
    PaymentMethod,
    PaymentStatus,
    PaymentStatusCode,
    User,
    UserCreate,
    VehicleType,
)

engine = create_engine(str(settings.DATABASE_URL), pool_pre_ping=True)


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28

# Tarifas de referencia del documento del proyecto: $5.000 COP carro, $2.800 COP
# moto (tarifa fija diaria). Se guardan en BD para que sean administrables.
VEHICLE_TYPES = [
    {"code": "car", "name": "Automóvil", "daily_rate_cop": 5000},
    {"code": "moto", "name": "Motocicleta", "daily_rate_cop": 2800},
]

PAYMENT_METHODS = [
    {"code": "card", "name": "Tarjeta débito/crédito"},
    {"code": "nequi", "name": "Nequi"},
    {"code": "pse", "name": "PSE"},
    {"code": "transfer", "name": "Transferencia"},
]

PAYMENT_STATUSES = [
    {"code": PaymentStatusCode.PENDING, "name": "Pendiente"},
    {"code": PaymentStatusCode.APPROVED, "name": "Aprobado"},
    {"code": PaymentStatusCode.DECLINED, "name": "Rechazado"},
    {"code": PaymentStatusCode.CANCELLED, "name": "Cancelado"},
]


def _seed_catalog(session: Session, model: type, rows: list[dict]) -> None:
    for row in rows:
        existing = session.exec(
            select(model).where(model.code == row["code"])
        ).first()
        if not existing:
            session.add(model(**row))
    session.commit()


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)

    _seed_catalog(session, VehicleType, VEHICLE_TYPES)
    _seed_catalog(session, PaymentMethod, PAYMENT_METHODS)
    _seed_catalog(session, PaymentStatus, PAYMENT_STATUSES)
