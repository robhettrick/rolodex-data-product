import json

from pydantic import BaseModel

from app.config import settings

DEFAULT_USERS_DB = {
    "alice": {"password": "secret1", "roles": ["user"]},
    "bob": {"password": "secret2", "roles": ["admin", "user"]}
}

# Load users database from a JSON file path, fallback to hard-coded defaults
users_db_file = settings.USERS_DB_FILE
if users_db_file:
    with open(users_db_file, "r") as f:
        users_db = json.load(f)
else:
    users_db = DEFAULT_USERS_DB

class User(BaseModel):
    username: str
    password: str
    roles: list[str]

def authenticate_user(username: str, password: str):
    user = users_db.get(username)
    if not user or user['password'] != password:
        return None
    return User(username=username, password=user['password'], roles=user['roles'])
