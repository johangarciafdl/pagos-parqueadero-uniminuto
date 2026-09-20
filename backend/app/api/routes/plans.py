import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import (
    Plan,
    PlanCreate,
    PlanPublic,
    PlansPublic,
    PlanUpdate,
    Subscription,
    SubscriptionPublic,
)

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/", response_model=PlansPublic)
def list_plans(session: SessionDep) -> PlansPublic:
    plans = session.exec(select(Plan).where(Plan.active == True)).all()  # noqa: E712
    return PlansPublic(data=plans, count=len(plans))


@router.get(
    "/all",
    response_model=PlansPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def list_all_plans(session: SessionDep) -> PlansPublic:
    plans = session.exec(select(Plan)).all()
    return PlansPublic(data=plans, count=len(plans))


@router.post(
    "/",
    response_model=PlanPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def create_plan(session: SessionDep, plan_in: PlanCreate) -> Plan:
    plan = Plan.model_validate(plan_in)
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


@router.patch(
    "/{plan_id}",
    response_model=PlanPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def update_plan(session: SessionDep, plan_id: uuid.UUID, plan_in: PlanUpdate) -> Plan:
    plan = session.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan no encontrado")
    plan.sqlmodel_update(plan_in.model_dump(exclude_unset=True))
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


@router.get("/subscriptions/me", response_model=SubscriptionPublic | None)
def my_active_subscription(
    session: SessionDep, current_user: CurrentUser
) -> Subscription | None:
    return session.exec(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.active == True,  # noqa: E712
            Subscription.end_date >= date.today(),
        )
    ).first()
