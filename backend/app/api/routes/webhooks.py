import logging
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request
from sqlmodel import select

from app.api.deps import SessionDep
from app.core.wompi import verify_event_signature
from app.models import (
    ParkingLog,
    ParkingLogAction,
    Payment,
    PaymentConcept,
    PaymentStatus,
    PaymentStatusCode,
    Plan,
    Subscription,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Mapeo del status que reporta Wompi al catálogo interno de estados.
_WOMPI_STATUS_MAP = {
    "APPROVED": PaymentStatusCode.APPROVED,
    "DECLINED": PaymentStatusCode.DECLINED,
    "VOIDED": PaymentStatusCode.CANCELLED,
    "ERROR": PaymentStatusCode.DECLINED,
}

# Estados terminales: una vez alcanzados, un evento duplicado no debe
# reprocesarse (idempotencia).
_TERMINAL_STATUSES = {
    PaymentStatusCode.APPROVED,
    PaymentStatusCode.DECLINED,
    PaymentStatusCode.CANCELLED,
}


@router.post("/wompi")
async def wompi_webhook(request: Request, session: SessionDep) -> dict:
    event = await request.json()

    # Nunca confiar en el estado de un pago reportado por nadie que no sea
    # Wompi con una firma válida (constitución, principio I).
    if not verify_event_signature(event):
        logger.warning("Webhook de Wompi con firma inválida rechazado")
        raise HTTPException(400, "Firma inválida")

    if event.get("event") != "transaction.updated":
        return {"received": True}

    transaction = event["data"]["transaction"]
    reference = transaction.get("reference")
    wompi_status = transaction.get("status")

    payment = session.exec(
        select(Payment).where(Payment.wompi_reference == reference)
    ).first()
    if payment is None:
        logger.warning("Webhook para referencia desconocida: %s", reference)
        # 200 para que Wompi no siga reintentando un evento que no nos aplica.
        return {"received": True, "matched": False}

    current_status = session.get(PaymentStatus, payment.status_id)
    if current_status and current_status.code in _TERMINAL_STATUSES:
        # Idempotencia: ya se procesó un evento terminal para este pago.
        return {"received": True, "already_processed": True}

    new_code = _WOMPI_STATUS_MAP.get(wompi_status)
    if new_code is None:
        return {"received": True, "ignored_status": wompi_status}

    new_status = session.exec(
        select(PaymentStatus).where(PaymentStatus.code == new_code)
    ).first()
    if new_status is None:
        raise HTTPException(500, "Catálogo de estados no inicializado")

    payment.status_id = new_status.id
    payment.updated_at = datetime.now(UTC)
    session.add(payment)

    log_action = (
        ParkingLogAction.PAYMENT_APPROVED
        if new_code == PaymentStatusCode.APPROVED
        else ParkingLogAction.PAYMENT_DECLINED
    )
    session.add(
        ParkingLog(
            user_id=payment.user_id,
            payment_id=payment.id,
            action=log_action,
            detail=f"Wompi status={wompi_status}",
        )
    )

    if (
        new_code == PaymentStatusCode.APPROVED
        and payment.concept in (PaymentConcept.PLAN_PURCHASE, PaymentConcept.PLAN_RENEWAL)
        and payment.plan_id is not None
    ):
        _activate_or_renew_subscription(session, payment)

    session.commit()
    return {"received": True, "status": new_code.value}


def _activate_or_renew_subscription(session: SessionDep, payment: Payment) -> None:
    plan = session.get(Plan, payment.plan_id)
    if plan is None:
        return

    today = date.today()
    existing = session.exec(
        select(Subscription).where(
            Subscription.user_id == payment.user_id,
            Subscription.plan_id == payment.plan_id,
            Subscription.active == True,  # noqa: E712
        )
    ).first()

    if existing and existing.end_date >= today:
        # Renovación: se extiende desde el vencimiento anterior, nunca desde
        # hoy, para no perder días ya pagados.
        existing.end_date = existing.end_date + timedelta(days=plan.duration_days)
        session.add(existing)
        action = ParkingLogAction.PLAN_RENEWED
    else:
        subscription = Subscription(
            user_id=payment.user_id,
            plan_id=plan.id,
            payment_id=payment.id,
            start_date=today,
            end_date=today + timedelta(days=plan.duration_days),
            active=True,
        )
        session.add(subscription)
        action = ParkingLogAction.PLAN_ACTIVATED

    session.add(
        ParkingLog(
            user_id=payment.user_id,
            payment_id=payment.id,
            action=action,
            detail=f"plan={plan.name}",
        )
    )
