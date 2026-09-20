"""Notificaciones push (Web Push API) al navegador/teléfono del estudiante,
para avisos del plan mensual tipo "tu plan vence en 3 días" o "se renovó tu
plan" (igual que una app de streaming avisa por una suscripción).

Si no hay llaves VAPID configuradas, se omite el envío en silencio: las
notificaciones son una mejora de experiencia, no algo de lo que dependa el
resto del sistema (pagos, planes, etc. funcionan igual sin esto).
"""

import logging
from datetime import date

from pywebpush import WebPushException, webpush
from sqlmodel import Session, select

from app.core.config import settings
from app.models import PushSubscription, User

logger = logging.getLogger(__name__)


def _send_to_user(session: Session, user: User, title: str, body: str) -> None:
    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        return

    subscriptions = session.exec(
        select(PushSubscription).where(PushSubscription.user_id == user.id)
    ).all()
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=f'{{"title": {title!r}, "body": {body!r}}}',
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.VAPID_CONTACT_EMAIL}"},
            )
        except WebPushException as exc:
            # Una suscripción vencida/inválida no debe tumbar el resto del
            # flujo (ej. el webhook de Wompi que dispara esta notificación).
            logger.warning("Push fallido para %s: %s", user.id, exc)
            if exc.response is not None and exc.response.status_code == 410:
                # 410 Gone: el navegador invalidó esa suscripción, se limpia.
                session.delete(sub)
                session.commit()


def notify_plan_renewed(session: Session, user: User, valid_until: date) -> None:
    _send_to_user(
        session,
        user,
        title="Tu plan se renovó ✅",
        body=f"Tu plan mensual queda activo hasta el {valid_until.isoformat()}.",
    )


def notify_plan_expiring_soon(session: Session, user: User, days_left: int) -> None:
    _send_to_user(
        session,
        user,
        title="Tu plan está por vencer",
        body=f"Tu plan mensual vence en {days_left} día(s). Renuévalo para no perder el acceso.",
    )
