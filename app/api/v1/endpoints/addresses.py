from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request
from sqlalchemy.orm import Session

from fastapi_jwt import JwtAuthorizationCredentials
from fastapi import Depends
from app.routes.auth import auth_scheme, require_roles

from app.db.session import SessionLocal
from app.models.address import Address
from app.models.party import Party
from app.models.party_address import PartyAddress
from app.schemas.address import AddressCreate, AddressRead
from app.schemas.hateoas import HypermediaModel
from app.schemas.party import PartyRead

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[HypermediaModel])
def read_addresses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db),
):
    require_roles(credentials, ["user"])
    addresses = db.query(Address).offset(skip).limit(limit).all()

    response = []
    for address in addresses:
        response.append({
            "data": AddressRead.from_orm(address),
            "links": create_address_links(request, address.address_id)
        })

    return response

def create_address_links(request: Request, address_id: int):
    base_url = str(request.base_url).rstrip('/')
    return [
        {"rel": "self", "href": f"{base_url}/addresses/{address_id}"},
        {"rel": "parties", "href": f"{base_url}/addresses/{address_id}/parties"},
    ]

@router.post("/", response_model=HypermediaModel)
def create_address(
    address: AddressCreate,
    request: Request,
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db),
):
    require_roles(credentials, ["user"])
    db_address = Address(**address.model_dump())
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return {
        "data": AddressRead.from_orm(db_address),
        "links": create_address_links(request, db_address.address_id)
    }

@router.get("/{address_id}", response_model=HypermediaModel)
def read_address(
    address_id: int,
    request: Request,
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db),
):
    require_roles(credentials, ["user"])
    db_address = db.query(Address).filter(Address.address_id == address_id).first()
    if db_address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    return {
        "data": AddressRead.from_orm(db_address),
        "links": create_address_links(request, db_address.address_id)
    }

@router.delete("/{address_id}", response_model=dict)
def delete_address(
    address_id: int,
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db),
):
    require_roles(credentials, ["user"])
    db_address = db.query(Address).filter(Address.address_id == address_id).first()
    if db_address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(db_address)
    db.commit()
    return {"detail": "Address successfully deleted"}

@router.get("/{address_id}/parties", response_model=dict)
def read_address_parties(
    address_id: int,
    request: Request,
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db),
):
    require_roles(credentials, ["user"])
    db_address = db.query(Address).filter(Address.address_id == address_id).first()
    if db_address is None:
        raise HTTPException(status_code=404, detail="Address not found")

    parties = (
        db.query(Party)
        .join(PartyAddress, Party.party_id == PartyAddress.party_id)
        .filter(PartyAddress.address_id == address_id)
        .all()
    )
    if not parties:
        raise HTTPException(status_code=404, detail="No parties found for this address")

    base_url = str(request.base_url).rstrip('/')
    party_entries = []
    for party in parties:
        party_entries.append({
            "data": PartyRead.from_orm(party),
            "links": [
                {"rel": "self", "href": f"{base_url}/parties/{party.party_id}"},
                {"rel": "address", "href": f"{base_url}/addresses/{address_id}"}
            ]
        })

    return {
        "address_id": address_id,
        "parties": party_entries,
        "links": [
            {"rel": "self", "href": f"{base_url}/addresses/{address_id}/parties"},
            {"rel": "address", "href": f"{base_url}/addresses/{address_id}"}
        ]
    }