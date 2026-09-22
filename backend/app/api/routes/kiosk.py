import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core import security
from app.core.config import settings
from app.core.qr import create_qr_token, decode_qr_token, has_unlimited_access
from app.core.rate_limit import check_login_rate_limit, record_failed_login
from app.models import (
    GuestRegister,
    KioskRegister,
    KioskRegisterResponse,
    KioskSession,
    ParkingLog,
    ParkingLogAction,
    QRSession,
    StaffRegister,
    Token,
    User,
    UserPublic,
    Vehicle,
    VerifyQR,
)

router = APIRouter(prefix="/kiosk", tags=["kiosk"])


def _issue_token(user_id) -> Token:  # noqa: ANN001
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user_id, expires_delta=access_token_expires
        )
    )


@router.post("/register", response_model=KioskRegisterResponse)
def register(session: SessionDep, body: KioskRegister) -> KioskRegisterResponse:
    """Alta de un estudiante: sin contraseña, identificado por su ID.

    Devuelve el token de sesión y el qr_token (solo se entrega en claro esta
    vez; el QR generado con él es lo que el estudiante debe guardar para
    volver a entrar).
    """
    existing = crud.get_user_by_student_id(session=session, student_id=body.student_id)
    if existing:
        raise HTTPException(
            status_code=400, detail="Ya existe una cuenta con ese ID de estudiante"
        )
    user = crud.create_kiosk_user(session=session, data=body)
    return KioskRegisterResponse(
        token=_issue_token(user.id),
        qr_token=user.qr_token,
        user=UserPublic.model_validate(user),
    )


@router.post("/register-guest", response_model=KioskRegisterResponse)
def register_guest(session: SessionDep, body: GuestRegister) -> KioskRegisterResponse:
    """Alta de un invitado/visitante: se identifica con documento nacional
    (tipo + número), no con un carné de estudiante. Paga la misma tarifa
    que un estudiante.
    """
    existing = crud.get_user_by_student_id(
        session=session, student_id=body.document_number
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Ya existe una cuenta con ese documento"
        )
    user = crud.create_guest_user(session=session, data=body)
    return KioskRegisterResponse(
        token=_issue_token(user.id),
        qr_token=user.qr_token,
        user=UserPublic.model_validate(user),
    )


@router.post(
    "/register-staff",
    response_model=KioskRegisterResponse,
    dependencies=[Depends(get_current_active_superuser)],
)
def register_staff(session: SessionDep, body: StaffRegister) -> KioskRegisterResponse:
    """Alta de personal de UNIMINUTO exento de pago del parqueadero.

    Solo un administrador puede darla de alta.
    """
    existing = crud.get_user_by_student_id(session=session, student_id=body.student_id)
    if existing:
        raise HTTPException(
            status_code=400, detail="Ya existe una cuenta con ese ID"
        )
    user = crud.create_staff_user(session=session, data=body)
    return KioskRegisterResponse(
        token=_issue_token(user.id),
        qr_token=user.qr_token,
        user=UserPublic.model_validate(user),
    )


@router.post("/session", response_model=Token)
def session_by_student_id(
    request: Request, session: SessionDep, body: KioskSession
) -> Token:
    """Reingreso rápido con solo el ID de estudiante.

    Limitado por IP (misma protección que el login de administrador) porque,
    a diferencia del QR, un ID de estudiante puede ser adivinable.
    """
    check_login_rate_limit(request)
    user = crud.get_user_by_student_id(session=session, student_id=body.student_id)
    if not user or not user.is_active:
        record_failed_login(request)
        raise HTTPException(status_code=404, detail="No existe una cuenta con ese ID")
    return _issue_token(user.id)


@router.post("/qr-session", response_model=Token)
def session_by_qr(request: Request, session: SessionDep, body: QRSession) -> Token:
    """Reingreso mediante el QR personal (JWT firmado, no el ID en claro)."""
    check_login_rate_limit(request)
    user = crud.get_user_by_qr_token(session=session, qr_token=body.qr_token)
    if not user or not user.is_active:
        record_failed_login(request)
        raise HTTPException(status_code=404, detail="Código QR no válido")
    return _issue_token(user.id)


@router.get("/my-qr")
def my_qr(current_user: CurrentUser) -> dict:
    if not current_user.qr_token:
        raise HTTPException(404, "Esta cuenta no tiene un QR asociado")
    return {"qr_token": current_user.qr_token}


@router.post("/regenerate-qr")
def regenerate_qr(session: SessionDep, current_user: CurrentUser) -> dict:
    """Invalida el QR anterior (por si se perdió/compartió) y genera uno nuevo."""
    user = crud.regenerate_qr_token(session=session, user=current_user)
    return {"qr_token": user.qr_token}


@router.get("/vehicle-qr/{vehicle_id}")
def vehicle_qr(
    session: SessionDep, current_user: CurrentUser, vehicle_id: uuid.UUID
) -> dict:
    """QR de acceso para un vehículo puntual del usuario: mismos datos
    básicos que el QR de sesión, más la placa, para que el parqueadero
    identifique con qué vehículo entra (un usuario con varios vehículos
    genera un QR distinto por cada uno)."""
    vehicle = session.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.owner_id != current_user.id:
        raise HTTPException(404, "Vehículo no encontrado")
    return {
        "qr_token": create_qr_token(current_user, plate=vehicle.plate),
        "plate": vehicle.plate,
    }


@router.post(
    "/verify-qr", dependencies=[Depends(get_current_active_superuser)]
)
def verify_qr(session: SessionDep, body: VerifyQR) -> dict:
    """Lector virtual del parqueadero: decodifica el QR (mismo formato que
    el lector físico real: nombre/apellido/rol/documento) y decide si se
    permite el paso sin cobro (exento o con plan vigente).

    Si se informa `direction`, además deja un registro de entrada/salida
    en la bitácora del usuario (el control físico de la barrera sigue
    siendo del sistema original de UNIMINUTO; esto es solo trazabilidad).

    Reservado a personal del parqueadero (cuenta de administrador) porque
    expone datos personales de quien presente el QR.
    """
    payload = decode_qr_token(body.qr_token)
    if not payload:
        raise HTTPException(400, "QR inválido o expirado")

    if body.direction and payload["sub"]:
        try:
            user_id = uuid.UUID(payload["sub"])
        except ValueError:
            user_id = None
        if user_id and session.get(User, user_id):
            action = (
                ParkingLogAction.ACCESS_ENTRY
                if body.direction == "entrada"
                else ParkingLogAction.ACCESS_EXIT
            )
            detail = (
                f"Placa {payload['placa']}" if payload["placa"] else "Sin vehículo asociado"
            )
            session.add(ParkingLog(user_id=user_id, action=action, detail=detail))
            session.commit()

    return {
        "nombre": payload["nombre"],
        "apellido": payload["apellido"],
        "rol": payload["rol"],
        "documento": payload["documento"],
        "plan_until": payload["plan_until"],
        "placa": payload["placa"],
        "acceso_libre": has_unlimited_access(payload),
    }
