import uuid
from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import EmailStr
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Users (auth) — reutilizado del template, solo se quita la relación con Item
# ---------------------------------------------------------------------------

# La sesión de un estudiante se identifica por su ID/carné (sin contraseña),
# pensado para un flujo de kiosco: escribes tu ID (o escaneas tu QR) y ya
# tienes acceso a pago/planes/historial/soporte. El correo+contraseña se deja
# reservado para el administrador (permisos elevados, sí requiere contraseña).
class UserRole(StrEnum):
    ESTUDIANTE = "ESTUDIANTE"
    EXENTO = "EXENTO"  # personal de UNIMINUTO exento de pago del parqueadero


class UserBase(SQLModel):
    email: EmailStr | None = Field(
        default=None, unique=True, index=True, max_length=255
    )
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=150)
    student_id: str | None = Field(
        default=None, unique=True, index=True, max_length=20
    )
    role: UserRole = UserRole.ESTUDIANTE
    # Fecha hasta la que tiene un plan mensual activo (o None). Se cachea acá
    # ademas de en Subscription para poder incluirla en el QR sin una
    # consulta adicional y para que el lector del parqueadero pueda validar
    # sin depender de la base de datos.
    plan_until: date | None = None


class UserCreate(UserBase):
    """Solo para cuentas administradas (superusuario / admin), con contraseña."""

    email: EmailStr = Field(unique=True, index=True, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class KioskRegister(SQLModel):
    """Alta de un estudiante: sin contraseña, solo su ID y nombre."""

    student_id: str = Field(min_length=1, max_length=20)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=150)


class StaffRegister(SQLModel):
    """Alta de personal de UNIMINUTO exento de pago (solo un admin puede crearla)."""

    student_id: str = Field(min_length=1, max_length=20)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=150)


class KioskSession(SQLModel):
    student_id: str = Field(min_length=1, max_length=20)


class QRSession(SQLModel):
    qr_token: str = Field(min_length=1, max_length=2000)


class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=150)
    student_id: str | None = Field(default=None, max_length=20)
    role: UserRole | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str | None = Field(default=None)
    # El QR es un JWT firmado (header/payload/firma) con la identidad del
    # usuario (nombre, apellido, rol, documento) — mismo formato que usa el
    # lector físico real del parqueadero, aunque firmado con nuestra propia
    # llave (no tenemos la de UNIMINUTO). Se guarda el último emitido para
    # poder invalidar uno anterior al regenerarlo.
    qr_token: str | None = Field(default=None, index=True, max_length=2000)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    vehicles: list[Vehicle] = Relationship(back_populates="owner", cascade_delete=True)
    payments: list[Payment] = Relationship(back_populates="user", cascade_delete=True)
    subscriptions: list[Subscription] = Relationship(
        back_populates="user", cascade_delete=True
    )
    support_tickets: list[SupportTicket] = Relationship(
        back_populates="user", cascade_delete=True
    )
    push_subscriptions: list[PushSubscription] = Relationship(
        back_populates="user", cascade_delete=True
    )


class UserPublic(SQLModel):
    id: uuid.UUID
    email: EmailStr | None = None
    is_active: bool
    is_superuser: bool
    full_name: str | None = None
    student_id: str | None = None
    role: UserRole
    plan_until: date | None = None
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# ---------------------------------------------------------------------------
# Catálogos — equivalentes a "types", "methods", "status" del sistema original
# Se guardan en BD (no como enum de código) para que las tarifas y catálogos
# sean administrables sin desplegar código nuevo.
# ---------------------------------------------------------------------------


class VehicleTypeBase(SQLModel):
    code: str = Field(unique=True, index=True, max_length=20)  # "car" | "moto"
    name: str = Field(max_length=100)
    daily_rate_cop: int = Field(ge=0)  # tarifa fija diaria, en pesos colombianos


class VehicleTypeCreate(VehicleTypeBase):
    pass


class VehicleTypeUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100)
    daily_rate_cop: int | None = Field(default=None, ge=0)


class VehicleType(VehicleTypeBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class VehicleTypePublic(VehicleTypeBase):
    id: uuid.UUID


class PaymentMethodBase(SQLModel):
    code: str = Field(unique=True, index=True, max_length=20)  # card|nequi|pse|transfer
    name: str = Field(max_length=100)
    enabled: bool = True


class PaymentMethod(PaymentMethodBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class PaymentMethodPublic(PaymentMethodBase):
    id: uuid.UUID


class PaymentStatusCode(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class PaymentStatusBase(SQLModel):
    code: PaymentStatusCode = Field(unique=True, index=True)
    name: str = Field(max_length=100)


class PaymentStatus(PaymentStatusBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class PaymentStatusPublic(PaymentStatusBase):
    id: uuid.UUID


# ---------------------------------------------------------------------------
# Vehículos / tarjetas
# ---------------------------------------------------------------------------


class VehicleBase(SQLModel):
    plate: str = Field(max_length=20, index=True)


class VehicleCreate(VehicleBase):
    type_id: uuid.UUID


class Vehicle(VehicleBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    type_id: uuid.UUID = Field(foreign_key="vehicletype.id", nullable=False)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)  # type: ignore
    )
    owner: User | None = Relationship(back_populates="vehicles")


class VehiclePublic(VehicleBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    type_id: uuid.UUID
    created_at: datetime | None = None


class VehiclesPublic(SQLModel):
    data: list[VehiclePublic]
    count: int


# ---------------------------------------------------------------------------
# Planes mensuales y suscripciones
# ---------------------------------------------------------------------------


class PlanBase(SQLModel):
    name: str = Field(max_length=100)
    price_cop: int = Field(ge=0)
    duration_days: int = Field(gt=0)
    conditions: str | None = Field(default=None, max_length=1000)
    # Disponible para comprar desde el primer momento (un solo plan para
    # todos los tipos de vehículo, no diferenciado por tipo). "Inactivo"
    # es el estado de la SUSCRIPCIÓN de cada usuario hasta que paga, no el
    # catálogo del plan. Un admin puede seguir desactivándolo si hace falta
    # retirarlo temporalmente de la venta.
    active: bool = True


class PlanCreate(PlanBase):
    vehicle_type_id: uuid.UUID | None = None


class PlanUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100)
    price_cop: int | None = Field(default=None, ge=0)
    duration_days: int | None = Field(default=None, gt=0)
    conditions: str | None = Field(default=None, max_length=1000)
    active: bool | None = None


class Plan(PlanBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    vehicle_type_id: uuid.UUID | None = Field(
        default=None, foreign_key="vehicletype.id", nullable=True
    )


class PlanPublic(PlanBase):
    id: uuid.UUID
    vehicle_type_id: uuid.UUID | None = None


class PlansPublic(SQLModel):
    data: list[PlanPublic]
    count: int


class Subscription(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    plan_id: uuid.UUID = Field(foreign_key="plan.id", nullable=False)
    payment_id: uuid.UUID | None = Field(
        default=None, foreign_key="payment.id", nullable=True
    )
    start_date: date
    end_date: date
    active: bool = True
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)  # type: ignore
    )
    user: User | None = Relationship(back_populates="subscriptions")


class SubscriptionPublic(SQLModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    start_date: date
    end_date: date
    active: bool


# ---------------------------------------------------------------------------
# Notificaciones push (Web Push API) — avisos tipo "tu plan vence en 3 días"
# o "tu plan se renovó", directo al teléfono/navegador del estudiante.
# ---------------------------------------------------------------------------


class PushSubscriptionCreate(SQLModel):
    endpoint: str = Field(max_length=1000)
    p256dh: str = Field(max_length=255)
    auth: str = Field(max_length=255)


class PushSubscription(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    endpoint: str = Field(unique=True, index=True, max_length=1000)
    p256dh: str = Field(max_length=255)
    auth: str = Field(max_length=255)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)  # type: ignore
    )
    user: User | None = Relationship(back_populates="push_subscriptions")


# ---------------------------------------------------------------------------
# Pagos — el monto y el estado NUNCA se reciben del cliente; se calculan y se
# confirman en el servidor (ver plan.md, sección "Integración Wompi").
# ---------------------------------------------------------------------------


class PaymentConcept(StrEnum):
    DAILY_FEE = "daily_fee"
    RECHARGE = "recharge"
    PLAN_PURCHASE = "plan_purchase"
    PLAN_RENEWAL = "plan_renewal"


class PaymentInitiate(SQLModel):
    """Lo único que el cliente puede pedir: qué quiere pagar, no cuánto ni el
    estado. La excepción es `amount_cop`, que solo se usa (y solo tiene
    sentido) para el concepto RECHARGE, donde el monto es una elección
    legítima del usuario; para cualquier otro concepto el servidor lo ignora
    y calcula el monto real a partir del catálogo correspondiente."""

    concept: PaymentConcept
    method_id: uuid.UUID
    vehicle_id: uuid.UUID | None = None
    plan_id: uuid.UUID | None = None
    amount_cop: int | None = Field(default=None, gt=0)


class Payment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    vehicle_id: uuid.UUID | None = Field(
        default=None, foreign_key="vehicle.id", nullable=True
    )
    plan_id: uuid.UUID | None = Field(default=None, foreign_key="plan.id", nullable=True)
    method_id: uuid.UUID = Field(foreign_key="paymentmethod.id", nullable=False)
    status_id: uuid.UUID = Field(foreign_key="paymentstatus.id", nullable=False)
    concept: PaymentConcept
    amount_cop: int = Field(ge=0)
    wompi_reference: str = Field(unique=True, index=True, max_length=100)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)  # type: ignore
    )
    updated_at: datetime | None = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)  # type: ignore
    )
    user: User | None = Relationship(back_populates="payments")


class PaymentPublic(SQLModel):
    id: uuid.UUID
    concept: PaymentConcept
    amount_cop: int
    method_code: str
    method_name: str
    status_code: PaymentStatusCode
    wompi_reference: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaymentsPublic(SQLModel):
    data: list[PaymentPublic]
    count: int


# ---------------------------------------------------------------------------
# Bitácora de trazabilidad — filas inmutables, nunca se editan ni se borran
# ---------------------------------------------------------------------------


class ParkingLogAction(StrEnum):
    PAYMENT_CREATED = "payment_created"
    PAYMENT_APPROVED = "payment_approved"
    PAYMENT_DECLINED = "payment_declined"
    PLAN_ACTIVATED = "plan_activated"
    PLAN_RENEWED = "plan_renewed"


class ParkingLog(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    payment_id: uuid.UUID | None = Field(
        default=None, foreign_key="payment.id", nullable=True
    )
    action: ParkingLogAction
    detail: str | None = Field(default=None, max_length=500)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)  # type: ignore
    )


class ParkingLogPublic(SQLModel):
    id: uuid.UUID
    payment_id: uuid.UUID | None
    action: ParkingLogAction
    detail: str | None
    created_at: datetime | None = None


class ParkingLogsPublic(SQLModel):
    data: list[ParkingLogPublic]
    count: int


# ---------------------------------------------------------------------------
# FAQ y soporte
# ---------------------------------------------------------------------------


class FAQBase(SQLModel):
    category: str = Field(max_length=100, index=True)
    question: str = Field(max_length=255)
    answer: str = Field(max_length=2000)
    display_order: int = 0


class FAQCreate(FAQBase):
    pass


class FAQUpdate(SQLModel):
    category: str | None = Field(default=None, max_length=100)
    question: str | None = Field(default=None, max_length=255)
    answer: str | None = Field(default=None, max_length=2000)
    display_order: int | None = None


class FAQ(FAQBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class FAQPublic(FAQBase):
    id: uuid.UUID


class FAQsPublic(SQLModel):
    data: list[FAQPublic]
    count: int


class SupportTicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportTicketCreate(SQLModel):
    subject: str = Field(max_length=255)
    message: str = Field(max_length=2000)


class SupportTicketUpdateStatus(SQLModel):
    status: SupportTicketStatus


class SupportTicketReply(SQLModel):
    admin_reply: str = Field(min_length=1, max_length=2000)


class SupportTicket(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    case_number: str = Field(unique=True, index=True, max_length=20)
    subject: str = Field(max_length=255)
    message: str = Field(max_length=2000)
    status: SupportTicketStatus = SupportTicketStatus.OPEN
    admin_reply: str | None = Field(default=None, max_length=2000)
    replied_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))  # type: ignore
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)  # type: ignore
    )
    updated_at: datetime | None = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)  # type: ignore
    )
    user: User | None = Relationship(back_populates="support_tickets")


class SupportTicketPublic(SQLModel):
    id: uuid.UUID
    case_number: str
    subject: str
    message: str
    status: SupportTicketStatus
    admin_reply: str | None = None
    replied_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SupportTicketsPublic(SQLModel):
    data: list[SupportTicketPublic]
    count: int


class SupportTicketAdminPublic(SupportTicketPublic):
    student_id: str | None = None
    user_full_name: str | None = None


class SupportTicketsAdminPublic(SQLModel):
    data: list[SupportTicketAdminPublic]
    count: int


# ---------------------------------------------------------------------------
# Genéricos (auth) — reutilizados del template
# ---------------------------------------------------------------------------


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class KioskRegisterResponse(SQLModel):
    token: Token
    qr_token: str
    user: UserPublic


class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
