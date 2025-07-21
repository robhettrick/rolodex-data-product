from typing import List

from fastapi import APIRouter, HTTPException, Request
from fastapi import Depends
from fastapi_jwt import JwtAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.party_relationship import PartyRelationship
from app.routes.auth import require_roles, auth_scheme
from app.schemas.hateoas import HypermediaModel
from app.schemas.party_relationship import PartyRelationshipCreate, PartyRelationshipRead

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[HypermediaModel])
def read_party_relationships(skip: int = 0, limit: int = 100, request: Request = None, credentials: JwtAuthorizationCredentials = Depends(auth_scheme), db: Session = Depends(get_db)):
    require_roles(credentials, ["user"])
    relationships = db.query(PartyRelationship).offset(skip).limit(limit).all()
    base_url = str(request.base_url).rstrip('/')
    pr_list = []
    for pr in relationships:
        pr_data = PartyRelationshipRead.from_orm(pr)
        pr_list.append({
            "data": pr_data,
            "links": [
                {"rel": "self", "href": f"{base_url}/party-relationships/{pr.relationship_id}"},
                {"rel": "from_party", "href": f"{base_url}/parties/{pr.from_party_id}"},
                {"rel": "to_party", "href": f"{base_url}/parties/{pr.to_party_id}"}
            ]
        })
    return pr_list

@router.post("/", response_model=HypermediaModel)
def create_party_relationship(request: Request, pr: PartyRelationshipCreate, credentials: JwtAuthorizationCredentials = Depends(auth_scheme), db: Session = Depends(get_db)):
    require_roles(credentials, ["user"])
    db_pr = PartyRelationship(**pr.model_dump())
    db.add(db_pr)
    db.commit()
    db.refresh(db_pr)
    pr_data = PartyRelationshipRead.from_orm(db_pr)
    base_url = str(request.base_url).rstrip('/')
    return {
        "data": pr_data,
        "links": [
            {"rel": "self", "href": f"{base_url}/party-relationships/{db_pr.relationship_id}"},
            {"rel": "from_party", "href": f"{base_url}/parties/{db_pr.from_party_id}"},
            {"rel": "to_party", "href": f"{base_url}/parties/{db_pr.to_party_id}"}
        ]
    }

@router.get("/{relationship_id}", response_model=HypermediaModel)
def read_party_relationship(relationship_id: int, request: Request, credentials: JwtAuthorizationCredentials = Depends(auth_scheme), db: Session = Depends(get_db)):
    require_roles(credentials, ["user"])
    db_pr = db.query(PartyRelationship).filter(PartyRelationship.relationship_id == relationship_id).first()
    if db_pr is None:
        raise HTTPException(status_code=404, detail="PartyRelationship not found")
    pr_data = PartyRelationshipRead.from_orm(db_pr)
    base_url = str(request.base_url).rstrip('/')
    return {
        "data": pr_data,
        "links": [
            {"rel": "self", "href": f"{base_url}/party-relationships/{db_pr.relationship_id}"},
            {"rel": "from_party", "href": f"{base_url}/parties/{db_pr.from_party_id}"},
            {"rel": "to_party", "href": f"{base_url}/parties/{db_pr.to_party_id}"}
        ]
    }

@router.delete("/{relationship_id}", response_model=HypermediaModel)
def delete_party_relationship(relationship_id: int, request: Request, credentials: JwtAuthorizationCredentials = Depends(auth_scheme), db: Session = Depends(get_db)):
    require_roles(credentials, ["user"])
    db_pr = db.query(PartyRelationship).filter(PartyRelationship.relationship_id == relationship_id).first()
    if db_pr is None:
        raise HTTPException(status_code=404, detail="PartyRelationship not found")
    pr_data = PartyRelationshipRead.from_orm(db_pr)
    base_url = str(request.base_url).rstrip('/')
    db.delete(db_pr)
    db.commit()
    return {
        "data": pr_data,
        "links": [
            {"rel": "self", "href": f"{base_url}/party-relationships/{db_pr.relationship_id}"},
            {"rel": "from_party", "href": f"{base_url}/parties/{db_pr.from_party_id}"},
            {"rel": "to_party", "href": f"{base_url}/parties/{db_pr.to_party_id}"}
        ]
    }