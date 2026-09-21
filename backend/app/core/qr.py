"""QR de identidad del estudiante/personal, con el mismo formato (JWT:
header/payload/firma) que usa el lector físico real del parqueadero de
UNIMINUTO — aunque firmado con nuestra propia llave, ya que no tenemos
acceso a la llave real del sistema institucional (esa integración
requeriría que UNIMINUTO nos la entregue oficialmente).

Claims del payload, alineados 1:1 con lo que decodifica el lector real:
nombre, apellido, rol, documento. Se agrega ademas `plan_until` (fecha
hasta la que tiene un plan mensual activo, o null) para que un lector -
incluso sin conexión a nuestra base de datos - pueda decidir si dejar
pasar sin cobro diario.
"""

from datetime import UTC, date, datetime, timedelta
from typing import TypedDict

import jwt

from app.core.config import settings
from app.models import User, UserRole

ALGORITHM = "HS256"
# Vigencia técnica del JWT en sí (no confundir con `plan_until`, que es la
# vigencia real del beneficio). Suficientemente larga para no forzar
# regeneraciones frecuentes; se puede regenerar en cualquier momento desde
# Ajustes si se pierde o se quiere invalidar.
QR_VALIDITY = timedelta(days=180)


class QRPayload(TypedDict):
    sub: str
    nombre: str
    apellido: str
    rol: str
    documento: str
    plan_until: str | None
    placa: str | None


def create_qr_token(user: User, plate: str | None = None) -> str:
    now = datetime.now(UTC)
    payload: QRPayload = {
        "sub": str(user.id),
        "nombre": user.first_name or (user.full_name or "").split(" ")[0],
        "apellido": user.last_name
        or " ".join((user.full_name or "").split(" ")[1:]),
        "rol": user.role.value,
        "documento": user.student_id or "",
        "plan_until": user.plan_until.isoformat() if user.plan_until else None,
        "placa": plate,
    }
    return jwt.encode(
        {**payload, "iat": now, "exp": now + QR_VALIDITY},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_qr_token(token: str) -> QRPayload | None:
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    return {
        "sub": decoded.get("sub", ""),
        "nombre": decoded.get("nombre", ""),
        "apellido": decoded.get("apellido", ""),
        "rol": decoded.get("rol", UserRole.ESTUDIANTE.value),
        "documento": decoded.get("documento", ""),
        "plan_until": decoded.get("plan_until"),
        "placa": decoded.get("placa"),
    }


def has_unlimited_access(payload: QRPayload) -> bool:
    """True si el portador puede entrar sin pago (exento o plan vigente)."""
    if payload["rol"] == UserRole.EXENTO.value:
        return True
    plan_until = payload.get("plan_until")
    if not plan_until:
        return False
    return date.fromisoformat(plan_until) >= date.today()
