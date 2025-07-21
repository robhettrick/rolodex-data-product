from typing import List

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi import Depends
from fastapi_jwt import JwtAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.external_identifier import ExternalIdentifier
from app.models.organisation import Organisation
from app.models.outbox_event import OutboxEvent
from app.models.party import Party
from app.routes.auth import auth_scheme, require_roles
from app.schemas.hateoas import HypermediaModel
from app.schemas.organisation import OrganisationCreate, OrganisationRead

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[HypermediaModel])
def read_organisations(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme),
):
    require_roles(credentials, ["user"])
    organisations = db.query(Organisation).offset(skip).limit(limit).all()

    response = []
    for org in organisations:
        response.append({
            "data": OrganisationRead.from_orm(org),
            "links": create_organisation_links(request, org.party_id)
        })

    return response


def create_organisation_links(request: Request, party_id: int):
    base_url = str(request.base_url).rstrip('/')
    return [
        {"rel": "self", "href": f"{base_url}/organisations/{party_id}"},
        {"rel": "party", "href": f"{base_url}/parties/{party_id}"},
        {"rel": "addresses", "href": f"{base_url}/parties/{party_id}/addresses"},
        {"rel": "relationships", "href": f"{base_url}/parties/{party_id}/relationships"},
        {"rel": "legacy-identifiers", "href": f"{base_url}/parties/{party_id}/legacy-identifiers"},
    ]

@router.post("/", response_model=HypermediaModel)
def create_organisation(
    org: OrganisationCreate,
    request: Request,
    db: Session = Depends(get_db),
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme),
):
    require_roles(credentials, ["user"])
    party = Party(party_type="organisation", display_name=org.organisation_name)
    db.add(party)
    db.commit()
    db.refresh(party)

    db_org = Organisation(party_id=party.party_id, **org.model_dump())
    db.add(db_org)
    db.commit()
    db.refresh(db_org)

    # Emit outbox event for creation
    outbox_event = OutboxEvent(
        event_type="OrganisationCreated",
        payload={
            "party_id": db_org.party_id,
            "organisation_name": org.organisation_name
        }
    )
    db.add(outbox_event)
    db.commit()

    return {
        "data": OrganisationRead.from_orm(db_org),
        "links": create_organisation_links(request, db_org.party_id)
    }

@router.get("/{party_id}", response_model=HypermediaModel)
def read_organisation(
    party_id: int,
    request: Request,
    db: Session = Depends(get_db),
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme),
):
    require_roles(credentials, ["user"])
    db_org = db.query(Organisation).filter(Organisation.party_id == party_id).first()
    if db_org is None:
        raise HTTPException(status_code=404, detail="Organisation not found")

    return {
        "data": OrganisationRead.from_orm(db_org),
        "links": create_organisation_links(request, db_org.party_id)
    }


# Update organisation endpoint
@router.put("/{party_id}", response_model=HypermediaModel)
def update_organisation(
    party_id: int,
    org_update: OrganisationCreate,
    request: Request,
    db: Session = Depends(get_db),
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme),
):
    require_roles(credentials, ["user"])
    db_org = db.query(Organisation).filter(Organisation.party_id == party_id).first()
    if not db_org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    # Update organisation fields
    db_org.organisation_name = org_update.organisation_name
    # Update party display_name
    party = db.query(Party).filter(Party.party_id == party_id).first()
    if party:
        party.display_name = org_update.organisation_name
    # Gather external identifiers
    identifiers = db.query(ExternalIdentifier).filter(ExternalIdentifier.party_id == party_id).all()
    ext_ids = [
        {"system_name": ei.system_name, "external_id": ei.external_id}
        for ei in identifiers
    ]
    # Emit outbox event for update
    outbox_event = OutboxEvent(
        event_type="OrganisationUpdated",
        payload={
            "party_id": party_id,
            "organisation_name": org_update.organisation_name,
            "external_identifiers": ext_ids
        }
    )
    db.add(outbox_event)
    # Commit all changes
    db.commit()
    db.refresh(db_org)
    return {
        "data": OrganisationRead.from_orm(db_org),
        "links": create_organisation_links(request, db_org.party_id)
    }


# Delete organisation endpoint
@router.delete("/{party_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organisation(
    party_id: int,
    request: Request,
    db: Session = Depends(get_db),
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme),
):
    require_roles(credentials, ["user"])
    db_org = db.query(Organisation).filter(Organisation.party_id == party_id).first()
    if not db_org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    # Gather external identifiers
    identifiers = db.query(ExternalIdentifier).filter(ExternalIdentifier.party_id == party_id).all()
    ext_ids = [
        {"system_name": ei.system_name, "external_id": ei.external_id}
        for ei in identifiers
    ]
    # Emit outbox event for deletion
    outbox_event = OutboxEvent(
        event_type="OrganisationDeleted",
        payload={
            "party_id": party_id,
            "external_identifiers": ext_ids
        }
    )
    db.add(outbox_event)
    # Remove organisation and party records
    db.delete(db_org)
    party = db.query(Party).filter(Party.party_id == party_id).first()
    if party:
        db.delete(party)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)