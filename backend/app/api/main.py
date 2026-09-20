from fastapi import APIRouter

from app.api.routes import (
    faq,
    history,
    login,
    payments,
    plans,
    private,
    support,
    users,
    utils,
    vehicles,
    webhooks,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(vehicles.router)
api_router.include_router(payments.router)
api_router.include_router(webhooks.router)
api_router.include_router(plans.router)
api_router.include_router(history.router)
api_router.include_router(faq.router)
api_router.include_router(support.router)


if settings.FASTAPI_ENV == "development":
    api_router.include_router(private.router)
