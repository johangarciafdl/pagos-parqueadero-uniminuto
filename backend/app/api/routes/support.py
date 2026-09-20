import secrets
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import (
    SupportTicket,
    SupportTicketCreate,
    SupportTicketPublic,
    SupportTicketsPublic,
    SupportTicketUpdateStatus,
)

router = APIRouter(prefix="/support", tags=["support"])


def _generate_case_number() -> str:
    # 8 caracteres alfanuméricos en mayúsculas, suficientemente únicos para
    # un volumen de soporte universitario; el índice único en BD es la
    # garantía real contra colisiones.
    return "CASE-" + secrets.token_hex(4).upper()


@router.post("/", response_model=SupportTicketPublic)
def create_ticket(
    session: SessionDep, current_user: CurrentUser, body: SupportTicketCreate
) -> SupportTicket:
    for _ in range(5):
        case_number = _generate_case_number()
        exists = session.exec(
            select(SupportTicket).where(SupportTicket.case_number == case_number)
        ).first()
        if not exists:
            break
    else:
        raise HTTPException(500, "No se pudo generar un número de caso único")

    ticket = SupportTicket(
        user_id=current_user.id,
        case_number=case_number,
        subject=body.subject,
        message=body.message,
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


@router.get("/", response_model=SupportTicketsPublic)
def list_my_tickets(session: SessionDep, current_user: CurrentUser) -> SupportTicketsPublic:
    tickets = session.exec(
        select(SupportTicket)
        .where(SupportTicket.user_id == current_user.id)
        .order_by(SupportTicket.created_at.desc())  # type: ignore[union-attr]
    ).all()
    return SupportTicketsPublic(data=tickets, count=len(tickets))


@router.patch(
    "/{ticket_id}/status",
    response_model=SupportTicketPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def update_ticket_status(
    session: SessionDep, ticket_id: uuid.UUID, body: SupportTicketUpdateStatus
) -> SupportTicket:
    ticket = session.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Solicitud no encontrada")
    ticket.status = body.status
    ticket.updated_at = datetime.now(UTC)
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket
