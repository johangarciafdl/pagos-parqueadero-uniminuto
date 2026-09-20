"""Rate limiting simple en memoria para intentos fallidos de login.

Solo cuenta intentos fallidos (no logins exitosos), que es lo que realmente
importa contra fuerza bruta: un usuario legítimo que inicia sesión varias
veces seguidas (por ejemplo, varias pestañas o un test suite) no debe verse
bloqueado.

No requiere una dependencia nueva (Redis/slowapi) para no sumar más peso al
proyecto en la semana de entrega. Limitación conocida: al vivir en memoria
del proceso, no se comparte entre workers/réplicas; si el proyecto pasa a
producción con más de un worker, esto debería moverse a un backend
compartido (Redis) — se documenta como deuda técnica aceptada
conscientemente (constitución, sección de Governance).
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request

_WINDOW_SECONDS = 60
_MAX_FAILED_ATTEMPTS = 5

_failed_attempts: dict[str, list[float]] = defaultdict(list)


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _recent(key: str) -> list[float]:
    now = time.monotonic()
    recent = [t for t in _failed_attempts[key] if now - t < _WINDOW_SECONDS]
    _failed_attempts[key] = recent
    return recent


def check_login_rate_limit(request: Request) -> None:
    key = _client_key(request)
    if len(_recent(key)) >= _MAX_FAILED_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos fallidos de inicio de sesión. Intenta más tarde.",
        )


def record_failed_login(request: Request) -> None:
    key = _client_key(request)
    _recent(key).append(time.monotonic())
