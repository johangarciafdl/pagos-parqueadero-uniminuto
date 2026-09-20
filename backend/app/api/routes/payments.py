import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.core.wompi import build_integrity_signature
from app.models import (
    ParkingLog,
    ParkingLogAction,
    Payment,
    PaymentConcept,
    PaymentInitiate,
    PaymentMethod,
    PaymentPublic,
    PaymentStatus,
    PaymentStatusCode,
    Plan,
    Vehicle,
    VehiclePublic,
    VehicleType,
)

router = APIRouter(prefix="/payments", tags=["payments"])


class PaymentInitiateResponse(PaymentPublic):
    wompi_public_key: str
    amount_in_cents: int
    integrity_signature: str
    redirect_url: str


def _get_status(session: SessionDep, code: PaymentStatusCode) -> PaymentStatus:
    status_row = session.exec(
        select(PaymentStatus).where(PaymentStatus.code == code)
    ).first()
    if status_row is None:
        raise HTTPException(500, "Catálogo de estados no inicializado")
    return status_row


def _resolve_amount_and_refs(
    *, session: SessionDep, user_id: uuid.UUID, body: PaymentInitiate
) -> tuple[int, uuid.UUID | None, uuid.UUID | None]:
    """Calcula el monto SIEMPRE en el servidor; el cliente nunca lo decide,
    salvo en una recarga, donde el monto es por definición una elección
    legítima del usuario (no una tarifa)."""

    if body.concept == PaymentConcept.DAILY_FEE:
        if body.vehicle_id is None:
            raise HTTPException(400, "vehicle_id es requerido para daily_fee")
        vehicle = session.get(Vehicle, body.vehicle_id)
        if not vehicle or vehicle.owner_id != user_id:
            raise HTTPException(404, "Vehículo no encontrado")
        vehicle_type = session.get(VehicleType, vehicle.type_id)
        if not vehicle_type:
            raise HTTPException(500, "Tipo de vehículo no configurado")
        return vehicle_type.daily_rate_cop, vehicle.id, None

    if body.concept in (PaymentConcept.PLAN_PURCHASE, PaymentConcept.PLAN_RENEWAL):
        if body.plan_id is None:
            raise HTTPException(400, "plan_id es requerido para planes")
        plan = session.get(Plan, body.plan_id)
        if not plan or not plan.active:
            raise HTTPException(404, "Plan no encontrado o inactivo")
        return plan.price_cop, None, plan.id

    if body.concept == PaymentConcept.RECHARGE:
        if body.amount_cop is None or body.amount_cop <= 0:
            raise HTTPException(400, "amount_cop es requerido para una recarga")
        vehicle_id = None
        if body.vehicle_id is not None:
            vehicle = session.get(Vehicle, body.vehicle_id)
            if not vehicle or vehicle.owner_id != user_id:
                raise HTTPException(404, "Vehículo no encontrado")
            vehicle_id = vehicle.id
        return body.amount_cop, vehicle_id, None

    raise HTTPException(400, "Concepto de pago no soportado")


@router.post("/", response_model=PaymentInitiateResponse)
def create_payment(
    session: SessionDep, current_user: CurrentUser, body: PaymentInitiate
) -> PaymentInitiateResponse:
    method = session.get(PaymentMethod, body.method_id)
    if not method or not method.enabled:
        raise HTTPException(400, "Método de pago no disponible")

    amount_cop, vehicle_id, plan_id = _resolve_amount_and_refs(
        session=session, user_id=current_user.id, body=body
    )
    pending_status = _get_status(session, PaymentStatusCode.PENDING)
    reference = f"PARK-{uuid.uuid4().hex[:20]}"

    payment = Payment(
        user_id=current_user.id,
        vehicle_id=vehicle_id,
        plan_id=plan_id,
        method_id=method.id,
        status_id=pending_status.id,
        concept=body.concept,
        amount_cop=amount_cop,
        wompi_reference=reference,
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)

    session.add(
        ParkingLog(
            user_id=current_user.id,
            payment_id=payment.id,
            action=ParkingLogAction.PAYMENT_CREATED,
            detail=f"{body.concept.value} por ${amount_cop} COP",
        )
    )
    session.commit()

    amount_in_cents = amount_cop * 100
    signature = build_integrity_signature(
        reference=reference, amount_in_cents=amount_in_cents
    )

    return PaymentInitiateResponse(
        id=payment.id,
        concept=payment.concept,
        amount_cop=payment.amount_cop,
        method_id=payment.method_id,
        status_id=payment.status_id,
        wompi_reference=payment.wompi_reference,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        wompi_public_key=settings.WOMPI_PUBLIC_KEY,
        amount_in_cents=amount_in_cents,
        integrity_signature=signature,
        redirect_url=f"/pagos/{payment.id}/resultado",
    )


@router.get("/pending", response_model=list[VehiclePublic])
def list_vehicles_with_pending_fee(
    session: SessionDep, current_user: CurrentUser
) -> list[Vehicle]:
    """Vehículos del usuario sin un pago de tarifa diaria aprobado hoy."""
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    vehicles = session.exec(
        select(Vehicle).where(Vehicle.owner_id == current_user.id)
    ).all()
    approved = _get_status(session, PaymentStatusCode.APPROVED)

    pending_vehicles = []
    for vehicle in vehicles:
        paid_today = session.exec(
            select(Payment).where(
                Payment.vehicle_id == vehicle.id,
                Payment.concept == PaymentConcept.DAILY_FEE,
                Payment.status_id == approved.id,
                Payment.created_at >= today_start,
            )
        ).first()
        if not paid_today:
            pending_vehicles.append(vehicle)
    return pending_vehicles


@router.get("/{payment_id}", response_model=PaymentPublic)
def get_payment(
    session: SessionDep, current_user: CurrentUser, payment_id: uuid.UUID
) -> Payment:
    payment = session.get(Payment, payment_id)
    if not payment or (
        payment.user_id != current_user.id and not current_user.is_superuser
    ):
        raise HTTPException(404, "Pago no encontrado")
    return payment
