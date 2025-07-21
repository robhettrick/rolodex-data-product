from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request
from fastapi_jwt import JwtAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.party_address import PartyAddress
from app.routes.auth import auth_scheme, require_roles
from app.schemas.hateoas import HypermediaModel
from app.schemas.party_address import PartyAddressCreate, PartyAddressRead

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=Union[HypermediaModel, List[HypermediaModel]])
def read_party_addresses(
    request: Request,
    party_id: int | None = None,
    address_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme)
):
    require_roles(credentials, ["user"])
    base_url = str(request.base_url).rstrip('/')
    # If both query params provided, return single resource
    if party_id is not None and address_id is not None:
        pa = db.query(PartyAddress).filter(
            PartyAddress.party_id == party_id,
            PartyAddress.address_id == address_id
        ).first()
        if pa is None:
            raise HTTPException(status_code=404, detail="PartyAddress not found")
        pa_data = PartyAddressRead.from_orm(pa)
        return {
            "data": pa_data,
            "links": [
                {"rel": "self", "href": f"{base_url}/party-addresses?party_id={pa.party_id}&address_id={pa.address_id}"},
                {"rel": "party", "href": f"{base_url}/parties/{pa.party_id}"},
                {"rel": "address", "href": f"{base_url}/addresses/{pa.address_id}"}
            ]
        }
    # Otherwise return list
    party_addresses = db.query(PartyAddress).offset(skip).limit(limit).all()
    pa_list = []
    for pa in party_addresses:
        pa_data = PartyAddressRead.from_orm(pa)
        pa_list.append({
            "data": pa_data,
            "links": [
                {"rel": "self", "href": f"{base_url}/party-addresses?party_id={pa.party_id}&address_id={pa.address_id}"},
                {"rel": "party", "href": f"{base_url}/parties/{pa.party_id}"},
                {"rel": "address", "href": f"{base_url}/addresses/{pa.address_id}"}
            ]
        })
    return pa_list

@router.post("/", response_model=HypermediaModel)
def create_party_address(pa: PartyAddressCreate, request: Request, db: Session = Depends(get_db), credentials: JwtAuthorizationCredentials = Depends(auth_scheme)):
    require_roles(credentials, ["user"])
    db_pa = PartyAddress(**pa.model_dump())
    db.add(db_pa)
    db.commit()
    db.refresh(db_pa)
    pa_data = PartyAddressRead.from_orm(db_pa)
    base_url = str(request.base_url).rstrip('/')
    return {
        "data": pa_data,
        "links": [
            {"rel": "self", "href": f"{base_url}/party-addresses?party_id={db_pa.party_id}&address_id={db_pa.address_id}"},
            {"rel": "party", "href": f"{base_url}/parties/{db_pa.party_id}"},
            {"rel": "address", "href": f"{base_url}/addresses/{db_pa.address_id}"}
        ]
    }

@router.delete("/", response_model=HypermediaModel)
def delete_party_address(pa: PartyAddressCreate, request: Request, db: Session = Depends(get_db), credentials: JwtAuthorizationCredentials = Depends(auth_scheme)):
    require_roles(credentials, ["user"])
    db_pa = db.query(PartyAddress).filter(
        PartyAddress.party_id == pa.party_id,
        PartyAddress.address_id == pa.address_id
    ).first()

    if db_pa is None:
        raise HTTPException(status_code=404, detail="PartyAddress not found")

    pa_data = PartyAddressRead.from_orm(db_pa)
    base_url = str(request.base_url).rstrip('/')

    db.delete(db_pa)
    db.commit()
    return {
        "data": pa_data,
        "links": [
            {"rel": "self", "href": f"{base_url}/party-addresses?party_id={db_pa.party_id}&address_id={db_pa.address_id}"},
            {"rel": "party", "href": f"{base_url}/parties/{db_pa.party_id}"},
            {"rel": "address", "href": f"{base_url}/addresses/{db_pa.address_id}"}
        ]
    }