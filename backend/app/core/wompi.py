"""Integración con la API de Wompi (sandbox/producción vía WOMPI_BASE_URL).

No se usa ningún SDK de terceros: no existe uno con respaldo de comunidad
confiable (ver investigación en specs/001-mvp-pagos-parqueadero/plan.md), así
que se llama la API REST directamente con httpx.
"""

import hashlib
import hmac

from app.core.config import settings


def build_integrity_signature(
    reference: str, amount_in_cents: int, currency: str = "COP"
) -> str:
    """Firma que el checkout de Wompi exige para confiar en el monto/referencia.

    Se calcula siempre en el servidor: el cliente nunca debe poder generarla,
    porque eso le permitiría alterar el monto a pagar.
    """
    raw = f"{reference}{amount_in_cents}{currency}{settings.WOMPI_INTEGRITY_SECRET}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_event_signature(event: dict) -> bool:
    """Verifica la firma de un evento de webhook de Wompi.

    Wompi indica en `signature.properties` qué campos de `data` concatenar
    (en ese orden), les agrega el timestamp del evento y el events secret, y
    compara el SHA256 resultante contra `signature.checksum`.
    Ref: https://docs.wompi.co/ -> "Verificación de eventos"
    """
    try:
        signature = event["signature"]
        properties: list[str] = signature["properties"]
        checksum: str = signature["checksum"]
        timestamp = event["timestamp"]
        data = event["data"]
    except (KeyError, TypeError):
        return False

    parts: list[str] = []
    for prop_path in properties:
        value: object = data
        for key in prop_path.split("."):
            if not isinstance(value, dict) or key not in value:
                return False
            value = value[key]
        parts.append(str(value))

    raw = "".join(parts) + str(timestamp) + settings.WOMPI_EVENTS_SECRET
    computed = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    # Comparación en tiempo constante: con `==` normal, el tiempo de
    # respuesta variaría según cuántos caracteres iniciales coinciden,
    # filtrando información que permitiría forjar un checksum válido
    # byte a byte (ataque de temporización) contra este endpoint público.
    return hmac.compare_digest(computed.lower(), str(checksum).lower())
