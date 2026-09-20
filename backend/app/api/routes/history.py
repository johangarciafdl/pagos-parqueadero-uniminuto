from datetime import date, datetime, time

from fastapi import APIRouter, Query
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.payments import to_payment_public
from app.models import (
    ParkingLog,
    ParkingLogsPublic,
    Payment,
    PaymentsPublic,
    PaymentStatus,
    PaymentStatusCode,
)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/", response_model=PaymentsPublic)
def get_payment_history(
    session: SessionDep,
    current_user: CurrentUser,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    status_code: PaymentStatusCode | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaymentsPublic:
    statement = select(Payment).where(Payment.user_id == current_user.id)

    if date_from is not None:
        statement = statement.where(
            Payment.created_at >= datetime.combine(date_from, time.min)
        )
    if date_to is not None:
        statement = statement.where(
            Payment.created_at <= datetime.combine(date_to, time.max)
        )
    if status_code is not None:
        status_row = session.exec(
            select(PaymentStatus).where(PaymentStatus.code == status_code)
        ).first()
        statement = statement.where(
            Payment.status_id == (status_row.id if status_row else None)
        )

    all_matching = session.exec(statement).all()
    count = len(all_matching)
    page = sorted(all_matching, key=lambda p: p.created_at or datetime.min, reverse=True)[
        offset : offset + limit
    ]
    return PaymentsPublic(
        data=[to_payment_public(session, p) for p in page], count=count
    )


@router.get("/log", response_model=ParkingLogsPublic)
def get_parking_log(
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = Query(default=50, le=200),
) -> ParkingLogsPublic:
    """Bitácora de trazabilidad cruda (para soporte/auditoría del propio
    usuario), complementaria al historial de pagos."""
    logs = session.exec(
        select(ParkingLog)
        .where(ParkingLog.user_id == current_user.id)
        .order_by(ParkingLog.created_at.desc())  # type: ignore[union-attr]
        .limit(limit)
    ).all()
    return ParkingLogsPublic(data=logs, count=len(logs))
