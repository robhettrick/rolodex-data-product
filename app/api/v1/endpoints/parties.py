from typing import List

from fastapi import APIRouter, HTTPException, Request
from fastapi import Depends
from fastapi_jwt import JwtAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.address import Address
from app.models.external_identifier import ExternalIdentifier
from app.models.party import Party
from app.models.party_address import PartyAddress
from app.models.party_relationship import PartyRelationship
from app.routes.auth import auth_scheme, require_roles
from app.schemas.address import AddressRead
from app.schemas.external_identifier import ExternalIdentifierRead
from app.schemas.hateoas import HypermediaModel
from app.schemas.party import PartyRead
from app.schemas.party_relationship import PartyRelationshipRead

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_party_links(request: Request, party: Party):
    base_url = str(request.base_url).rstrip('/')
    links = [
        {"rel": "self", "href": f"{base_url}/parties/{party.party_id}"},
        {"rel": "addresses", "href": f"{base_url}/parties/{party.party_id}/addresses"},
        {"rel": "relationships", "href": f"{base_url}/parties/{party.party_id}/relationships"},
        {"rel": "external-identifiers", "href": f"{base_url}/parties/{party.party_id}/external-identifiers"},
    ]

    # Explicitly link to subtype endpoints based on party_type
    if party.party_type == "person":
        links.append({"rel": "person", "href": f"{base_url}/persons/{party.party_id}"})
    elif party.party_type == "organisation":
        links.append({"rel": "organisation", "href": f"{base_url}/organisations/{party.party_id}"})

    return links

@router.get("/", response_model=List[HypermediaModel])
def read_parties(request: Request, skip: int = 0, limit: int = 100, credentials: JwtAuthorizationCredentials = Depends(auth_scheme), db: Session = Depends(get_db)):
    require_roles(credentials, ["user"])
    parties = db.query(Party).offset(skip).limit(limit).all()
    response = []
    for party in parties:
        response.append({
            "data": PartyRead.from_orm(party),
            "links": create_party_links(request, party)
        })
    return response

@router.get("/{party_id}", response_model=HypermediaModel)
def read_party(party_id: int, request: Request, credentials: JwtAuthorizationCredentials = Depends(auth_scheme), db: Session = Depends(get_db)):
    require_roles(credentials, ["user"])
    db_party = db.query(Party).filter(Party.party_id == party_id).first()
    if db_party is None:
        raise HTTPException(status_code=404, detail="Party not found")
    return {
        "data": PartyRead.from_orm(db_party),
        "links": create_party_links(request, db_party)
    }

@router.get("/{party_id}/addresses", response_model=dict)
def read_party_addresses(party_id: int, request: Request, credentials: JwtAuthorizationCredentials = Depends(auth_scheme), db: Session = Depends(get_db)):
    require_roles(credentials, ["user"])
    party = db.query(Party).filter(Party.party_id == party_id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")

    addresses = (
        db.query(Address)
        .join(PartyAddress, Address.address_id == PartyAddress.address_id)
        .filter(PartyAddress.party_id == party_id)
        .all()
    )

    if not addresses:
        raise HTTPException(status_code=404, detail="No addresses found for this party")

    base_url = str(request.base_url).rstrip('/')

    address_responses = []
    for address in addresses:
        address_responses.append({
            "data": AddressRead.from_orm(address),
            "links": [
                {"rel": "self", "href": f"{base_url}/addresses/{address.address_id}"},
                {"rel": "party", "href": f"{base_url}/parties/{party_id}"}
            ]
        })

    return {
        "party_id": party_id,
        "addresses": address_responses,
        "links": [
            {"rel": "self", "href": f"{base_url}/parties/{party_id}/addresses"},
            {"rel": "party", "href": f"{base_url}/parties/{party_id}"}
        ]
    }

@router.get("/{party_id}/relationships", response_model=dict)
def read_party_relationships(party_id: int, request: Request, credentials: JwtAuthorizationCredentials = Depends(auth_scheme), db: Session = Depends(get_db)):
    require_roles(credentials, ["user"])
    relationships = db.query(PartyRelationship).filter(
        (PartyRelationship.from_party_id == party_id) |
        (PartyRelationship.to_party_id == party_id)
    ).all()

    if not relationships:
        raise HTTPException(status_code=404, detail="No relationships found for this party")

    base_url = str(request.base_url).rstrip('/')

    relationship_responses = []
    for rel in relationships:
        relationship_responses.append({
            "data": PartyRelationshipRead.from_orm(rel),
            "links": [
                {"rel": "self", "href": f"{base_url}/party-relationships/{rel.relationship_id}"},
                {"rel": "from_party", "href": f"{base_url}/parties/{rel.from_party_id}"},
                {"rel": "to_party", "href": f"{base_url}/parties/{rel.to_party_id}"}
            ]
        })

    return {
        "party_id": party_id,
        "relationships": relationship_responses,
        "links": [
            {"rel": "self", "href": f"{base_url}/parties/{party_id}/relationships"},
            {"rel": "party", "href": f"{base_url}/parties/{party_id}"}
        ]
    }

@router.get("/{party_id}/external-identifiers", response_model=dict)
def read_party_external_identifiers(party_id: int, request: Request, credentials: JwtAuthorizationCredentials = Depends(auth_scheme), db: Session = Depends(get_db)):
    require_roles(credentials, ["user"])
    party = db.query(Party).filter(Party.party_id == party_id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")

    external_identifiers = (
        db.query(ExternalIdentifier)
        .filter(ExternalIdentifier.party_id == party_id)
        .all()
    )

    if not external_identifiers:
        raise HTTPException(status_code=404, detail="No external identifiers found for this party")

    base_url = str(request.base_url).rstrip('/')

    external_responses = []
    for ei in external_identifiers:
        external_responses.append({
            "data": ExternalIdentifierRead.from_orm(ei),
            "links": [
                {"rel": "self", "href": f"{base_url}/external-identifiers/{ei.external_identifier_id}"},
                {"rel": "party", "href": f"{base_url}/parties/{party_id}"}
            ]
        })

    return {
        "party_id": party_id,
        "legacy_identifiers": external_responses,
        "links": [
            {"rel": "self", "href": f"{base_url}/parties/{party_id}/external-identifiers"},
            {"rel": "party", "href": f"{base_url}/parties/{party_id}"}
        ]
    }