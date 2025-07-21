from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi_jwt import JwtAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.external_identifier import ExternalIdentifier
from app.models.outbox_event import OutboxEvent
from app.models.party import Party
from app.models.person import Person
from app.routes.auth import auth_scheme, require_roles
from app.schemas.hateoas import HypermediaModel
from app.schemas.person import PersonCreate, PersonRead

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[HypermediaModel])
def read_persons(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), credentials: JwtAuthorizationCredentials = Depends(auth_scheme)):
    require_roles(credentials, ["user"])
    persons = db.query(Person).offset(skip).limit(limit).all()

    response = []
    for person in persons:
        response.append({
            "data": PersonRead.from_orm(person),
            "links": create_person_links(request, person.party_id)
        })

    return response

@router.get("/{party_id}", response_model=HypermediaModel)
def read_person(party_id: int, request: Request, db: Session = Depends(get_db), credentials: JwtAuthorizationCredentials = Depends(auth_scheme)):
    require_roles(credentials, ["user"])
    db_person = db.query(Person).filter(Person.party_id == party_id).first()
    if db_person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    return {
        "data": PersonRead.from_orm(db_person),
        "links": create_person_links(request, db_person.party_id)
    }

def create_person_links(request: Request, party_id: int):
    base_url = str(request.base_url).rstrip('/')
    return [
        {"rel": "self", "href": f"{base_url}/persons/{party_id}"},
        {"rel": "party", "href": f"{base_url}/parties/{party_id}"},
        {"rel": "addresses", "href": f"{base_url}/parties/{party_id}/addresses"},
        {"rel": "relationships", "href": f"{base_url}/parties/{party_id}/relationships"},
        {"rel": "legacy-identifiers", "href": f"{base_url}/parties/{party_id}/legacy-identifiers"},
    ]

@router.post("/", response_model=HypermediaModel)
def create_person(
    person: PersonCreate,
    request: Request,
    db: Session = Depends(get_db),
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme)
):
    require_roles(credentials, ["user"])
    party = Party(party_type="person", display_name=f"{person.first_name} {person.last_name}")
    db.add(party)
    db.commit()
    db.refresh(party)

    db_person = Person(party_id=party.party_id, **person.model_dump())
    db.add(db_person)

    # Create outbox event explicitly
    outbox_event = OutboxEvent(
        event_type="PersonCreated",
        payload={
            "party_id": party.party_id,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "email": person.email
        }
    )
    db.add(outbox_event)

    db.commit()
    db.refresh(db_person)

    return {
        "data": PersonRead.from_orm(db_person),
        "links": create_person_links(request, db_person.party_id)
    }

@router.put(
    "/persons/{party_id}",
    response_model=HypermediaModel
)
def update_person(party_id: int, person_update: PersonCreate, request: Request, db: Session = Depends(get_db), credentials: JwtAuthorizationCredentials = Depends(auth_scheme)):
    require_roles(credentials, ["user"])
    # Retrieve the existing person record
    db_person = db.query(Person).filter(Person.party_id == party_id).first()
    if not db_person:
        raise HTTPException(status_code=404, detail="Person not found")

    # Update the person's fields
    db_person.first_name = person_update.first_name
    db_person.last_name = person_update.last_name
    db_person.email = person_update.email

    # Update the associated party's display_name
    party = db.query(Party).filter(Party.party_id == party_id).first()
    if party:
        party.display_name = f"{person_update.first_name} {person_update.last_name}"

    # Emit outbox event explicitly for the update
    # Gather external identifiers
    identifiers = db.query(ExternalIdentifier).filter(ExternalIdentifier.party_id == party_id).all()
    ext_ids = [
        {"system_name": ei.system_name, "external_id": ei.external_id}
        for ei in identifiers
    ]
    outbox_event = OutboxEvent(
        event_type="PersonUpdated",
        payload={
            "party_id": party_id,
            "first_name": person_update.first_name,
            "last_name": person_update.last_name,
            "email": person_update.email,
            "external_identifiers": ext_ids
        }
    )
    db.add(outbox_event)

    # Commit all changes
    db.commit()
    db.refresh(db_person)

    # Return HATEOAS response
    return {
        "data": PersonRead.from_orm(db_person),
        "links": create_person_links(request, db_person.party_id)
    }

# Delete a person endpoint
@router.delete(
  "/persons/{party_id}",
  status_code=status.HTTP_204_NO_CONTENT,
  response_model=None
)
def delete_person(party_id: int, request: Request, db: Session = Depends(get_db), credentials: JwtAuthorizationCredentials = Depends(auth_scheme)):
    require_roles(credentials, ["user"])
    # Ensure the person exists
    db_person = db.query(Person).filter(Person.party_id == party_id).first()
    if db_person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    # Gather external identifiers
    identifiers = db.query(ExternalIdentifier).filter(ExternalIdentifier.party_id == party_id).all()
    ext_ids = [
        {"system_name": ei.system_name, "external_id": ei.external_id}
        for ei in identifiers
    ]
    # Emit outbox event for deletion
    outbox_event = OutboxEvent(
        event_type="PersonDeleted",
        payload={
            "party_id": party_id,
            "external_identifiers": ext_ids
        }
    )
    db.add(outbox_event)
    # Remove the person and party records
    db.delete(db_person)
    party = db.query(Party).filter(Party.party_id == party_id).first()
    if party:
        db.delete(party)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
