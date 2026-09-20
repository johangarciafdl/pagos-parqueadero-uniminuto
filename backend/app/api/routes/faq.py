import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.models import FAQ, FAQCreate, FAQPublic, FAQsPublic, FAQUpdate

router = APIRouter(prefix="/faq", tags=["faq"])


@router.get("/", response_model=FAQsPublic)
def list_faq(session: SessionDep, category: str | None = None) -> FAQsPublic:
    statement = select(FAQ).order_by(FAQ.display_order)
    if category:
        statement = statement.where(FAQ.category == category)
    faqs = session.exec(statement).all()
    return FAQsPublic(data=faqs, count=len(faqs))


@router.post(
    "/", response_model=FAQPublic, dependencies=[Depends(get_current_active_superuser)]
)
def create_faq(session: SessionDep, faq_in: FAQCreate) -> FAQ:
    faq = FAQ.model_validate(faq_in)
    session.add(faq)
    session.commit()
    session.refresh(faq)
    return faq


@router.patch(
    "/{faq_id}",
    response_model=FAQPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def update_faq(session: SessionDep, faq_id: uuid.UUID, faq_in: FAQUpdate) -> FAQ:
    faq = session.get(FAQ, faq_id)
    if not faq:
        raise HTTPException(404, "Pregunta no encontrada")
    faq.sqlmodel_update(faq_in.model_dump(exclude_unset=True))
    session.add(faq)
    session.commit()
    session.refresh(faq)
    return faq


@router.delete(
    "/{faq_id}", dependencies=[Depends(get_current_active_superuser)]
)
def delete_faq(session: SessionDep, faq_id: uuid.UUID) -> dict:
    faq = session.get(FAQ, faq_id)
    if not faq:
        raise HTTPException(404, "Pregunta no encontrada")
    session.delete(faq)
    session.commit()
    return {"deleted": True}
