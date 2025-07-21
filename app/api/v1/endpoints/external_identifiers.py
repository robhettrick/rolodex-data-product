from typing import List

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi import Request
from fastapi_jwt import JwtAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.external_identifier import ExternalIdentifier
from app.routes.auth import auth_scheme, require_roles
from app.schemas.external_identifier import ExternalIdentifierCreate, ExternalIdentifierRead
from app.schemas.hateoas import HypermediaModel

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[HypermediaModel])
def read_external_identifiers(
    skip: int = 0,
    limit: int = 100,
    request: Request = None,
    db: Session = Depends(get_db),
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme)
):
    require_roles(credentials, ["user"])
    legacy_identifiers = db.query(ExternalIdentifier).offset(skip).limit(limit).all()
    base_url = str(request.base_url).rstrip('/')
    li_list = []
    for li in legacy_identifiers:
        li_data = ExternalIdentifierRead.from_orm(li)
        li_list.append({
            "data": li_data,
            "links": [
                {"rel": "self", "href": f"{base_url}/external-identifiers/{li.external_identifier_id}"},
                {"rel": "party", "href": f"{base_url}/parties/{li.party_id}"}
            ]
        })
    return li_list

@router.post("/", response_model=HypermediaModel)
def create_external_identifier(
    li: ExternalIdentifierCreate,
    request: Request,
    db: Session = Depends(get_db),
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme)
):
    require_roles(credentials, ["user"])
    db_li = ExternalIdentifier(**li.model_dump())
    db.add(db_li)
    db.commit()
    db.refresh(db_li)
    li_data = ExternalIdentifierRead.from_orm(db_li)
    base_url = str(request.base_url).rstrip('/')
    return {
        "data": li_data,
        "links": [
            {"rel": "self", "href": f"{base_url}/external-identifiers/{db_li.external_identifier_id}"},
            {"rel": "party", "href": f"{base_url}/parties/{db_li.party_id}"}
        ]
    }

@router.get("/{external_identifier_id}", response_model=HypermediaModel)
def read_external_identifier(
    external_identifier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme)
):
    require_roles(credentials, ["user"])
    db_li = db.query(ExternalIdentifier).filter(ExternalIdentifier.external_identifier_id == external_identifier_id).first()
    if db_li is None:
        raise HTTPException(status_code=404, detail="ExternalIdentifier not found")
    li_data = ExternalIdentifierRead.from_orm(db_li)
    base_url = str(request.base_url).rstrip('/')
    return {
        "data": li_data,
        "links": [
            {"rel": "self", "href": f"{base_url}/external-identifiers/{db_li.external_identifier_id}"},
            {"rel": "party", "href": f"{base_url}/parties/{db_li.party_id}"}
        ]
    }

@router.delete("/{external_identifier_id}", response_model=HypermediaModel)
def delete_external_identifier(
    external_identifier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    credentials: JwtAuthorizationCredentials = Depends(auth_scheme)
):
    require_roles(credentials, ["user"])
    db_li = db.query(ExternalIdentifier).filter(ExternalIdentifier.external_identifier_id == external_identifier_id).first()
    if db_li is None:
        raise HTTPException(status_code=404, detail="ExternalIdentifier not found")
    li_data = ExternalIdentifierRead.from_orm(db_li)
    base_url = str(request.base_url).rstrip('/')
    db.delete(db_li)
    db.commit()
    return {
        "data": li_data,
        "links": [
            {"rel": "self", "href": f"{base_url}/external-identifiers/{db_li.external_identifier_id}"},
            {"rel": "party", "href": f"{base_url}/parties/{db_li.party_id}"}
        ]
    }