from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi_jwt import JwtAccessBearer, JwtAuthorizationCredentials
from pydantic import BaseModel

from app.auth import authenticate_user
from app.config import settings

# Schema for login request
class LoginRequest(BaseModel):
    username: str
    password: str

auth_scheme = JwtAccessBearer(secret_key=settings.JWT_SECRET_KEY,
                              algorithm=settings.JWT_ALGORITHM,
                              access_expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

router = APIRouter()

def require_roles(credentials: JwtAuthorizationCredentials, required_roles: list[str]):
    # credentials.claims holds the decoded JWT claims
    token_data = credentials.subject
    user_roles = token_data.get("roles", [])
    if not set(required_roles).intersection(user_roles):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

@router.post("/login")
def login(login_req: LoginRequest):
    auth_user = authenticate_user(login_req.username, login_req.password)
    if not auth_user:
        raise HTTPException(status_code=401, detail="Bad username or password")

    # Create a token using the authenticated user's information
    token_data = {"username": auth_user.username, "roles": auth_user.roles}
    access_token = auth_scheme.create_access_token(subject=token_data)
    return {"access_token": access_token}

# Example of protected route usage
@router.get("/protected")
def protected_route(credentials: JwtAuthorizationCredentials = Depends(auth_scheme)):
    token_data = credentials.subject
    return {
        "username": token_data["username"],
        "roles": token_data["roles"]
    }