import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Vehicle,
    VehicleCreate,
    VehiclePublic,
    VehiclesPublic,
    VehicleType,
    VehicleTypePublic,
)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/", response_model=VehiclesPublic)
def list_my_vehicles(session: SessionDep, current_user: CurrentUser) -> VehiclesPublic:
    vehicles = session.exec(
        select(Vehicle).where(Vehicle.owner_id == current_user.id)
    ).all()
    return VehiclesPublic(data=vehicles, count=len(vehicles))


@router.post("/", response_model=VehiclePublic)
def register_vehicle(
    session: SessionDep, current_user: CurrentUser, body: VehicleCreate
) -> Vehicle:
    vehicle_type = session.get(VehicleType, body.type_id)
    if not vehicle_type:
        raise HTTPException(400, "Tipo de vehículo no válido")

    vehicle = Vehicle(
        plate=body.plate.strip().upper(),
        type_id=body.type_id,
        owner_id=current_user.id,
    )
    session.add(vehicle)
    session.commit()
    session.refresh(vehicle)
    return vehicle


@router.get("/types", response_model=list[VehicleTypePublic])
def list_vehicle_types(session: SessionDep) -> list[VehicleType]:
    return session.exec(select(VehicleType)).all()


@router.delete("/{vehicle_id}")
def delete_vehicle(
    session: SessionDep, current_user: CurrentUser, vehicle_id: uuid.UUID
) -> dict:
    vehicle = session.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.owner_id != current_user.id:
        raise HTTPException(404, "Vehículo no encontrado")
    session.delete(vehicle)
    session.commit()
    return {"deleted": True}
