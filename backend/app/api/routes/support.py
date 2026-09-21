import secrets
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import (
    SupportTicket,
    SupportTicketAdminPublic,
    SupportTicketCreate,
    SupportTicketPublic,
    SupportTicketReply,
    SupportTicketsAdminPublic,
    SupportTicketsPublic,
    SupportTicketStatus,
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


@router.get(
    "/all",
    response_model=SupportTicketsAdminPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def list_all_tickets(session: SessionDep) -> SupportTicketsAdminPublic:
    tickets = session.exec(
        select(SupportTicket).order_by(SupportTicket.created_at.desc())  # type: ignore[union-attr]
    ).all()
    data = [
        SupportTicketAdminPublic(
            **ticket.model_dump(),
            student_id=ticket.user.student_id if ticket.user else None,
            user_full_name=ticket.user.full_name if ticket.user else None,
        )
        for ticket in tickets
    ]
    return SupportTicketsAdminPublic(data=data, count=len(data))


@router.patch(
    "/{ticket_id}/reply",
    response_model=SupportTicketPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def reply_ticket(
    session: SessionDep, ticket_id: uuid.UUID, body: SupportTicketReply
) -> SupportTicket:
    ticket = session.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Solicitud no encontrada")
    now = datetime.now(UTC)
    ticket.admin_reply = body.admin_reply
    ticket.replied_at = now
    ticket.status = SupportTicketStatus.RESOLVED
    ticket.updated_at = now
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket
