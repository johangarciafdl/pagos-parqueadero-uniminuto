"""Endpoints llamados por un proceso externo (cron), no por usuarios.

Protegidos con un secreto compartido en el header `X-Cron-Secret` en vez de
un JWT de usuario, porque quien los llama no es una persona con sesión.
"""

from datetime import date, timedelta

from fastapi import APIRouter, Header, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep
from app.core.config import settings
from app.core.push import notify_plan_expiring_soon
from app.models import Subscription, User

router = APIRouter(prefix="/internal", tags=["internal"])

# Con cuántos días de anticipación se avisa que el plan está por vencer.
_REMINDER_DAYS_BEFORE = (3, 1)


def _require_cron_secret(x_cron_secret: str | None) -> None:
    if not settings.CRON_SECRET or x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(401, "No autorizado")


@router.post("/check-expiring-plans")
def check_expiring_plans(
    session: SessionDep, x_cron_secret: str | None = Header(default=None)
) -> dict:
    _require_cron_secret(x_cron_secret)

    notified = 0
    for days_left in _REMINDER_DAYS_BEFORE:
        target_date = date.today() + timedelta(days=days_left)
        subs = session.exec(
            select(Subscription).where(
                Subscription.active == True,  # noqa: E712
                Subscription.end_date == target_date,
            )
        ).all()
        for sub in subs:
            user = session.get(User, sub.user_id)
            if user:
                notify_plan_expiring_soon(session, user, days_left)
                notified += 1

    return {"checked": True, "notified": notified}
