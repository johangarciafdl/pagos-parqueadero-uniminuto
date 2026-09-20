from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.core import security
from app.core.config import settings
from app.core.rate_limit import check_login_rate_limit, record_failed_login
from app.models import (
    KioskRegister,
    KioskRegisterResponse,
    KioskSession,
    QRSession,
    Token,
    UserPublic,
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
    """Reingreso mediante el QR personal (token de alta entropía, no el ID)."""
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
