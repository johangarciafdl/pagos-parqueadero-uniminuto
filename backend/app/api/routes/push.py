from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import Message, PushSubscription, PushSubscriptionCreate

router = APIRouter(prefix="/push", tags=["push"])


@router.get("/public-key")
def get_public_key() -> dict:
    from app.core.config import settings

    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(404, "Las notificaciones push no están configuradas")
    return {"public_key": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe", response_model=Message)
def subscribe(
    session: SessionDep, current_user: CurrentUser, body: PushSubscriptionCreate
) -> Message:
    existing = session.exec(
        select(PushSubscription).where(PushSubscription.endpoint == body.endpoint)
    ).first()
    if existing:
        existing.p256dh = body.p256dh
        existing.auth = body.auth
        existing.user_id = current_user.id
        session.add(existing)
    else:
        session.add(
            PushSubscription(
                user_id=current_user.id,
                endpoint=body.endpoint,
                p256dh=body.p256dh,
                auth=body.auth,
            )
        )
    session.commit()
    return Message(message="Suscripción a notificaciones guardada")


@router.post("/unsubscribe", response_model=Message)
def unsubscribe(session: SessionDep, current_user: CurrentUser, endpoint: str) -> Message:
    sub = session.exec(
        select(PushSubscription).where(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == current_user.id,
        )
    ).first()
    if sub:
        session.delete(sub)
        session.commit()
    return Message(message="Suscripción eliminada")
