import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine
from datetime import date
import uuid

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

@pytest.fixture
def create_address():
    address_payload = {
        "address_line_1": "123 Test Street",
        "city": "Testville",
        "postal_code": "TST123",
        "country": "UK",
        "address_type": "Home"
    }
    response = client.post("/addresses/", json=address_payload)
    assert response.status_code == 200, response.text
    return response.json()

@pytest.fixture
def create_person():
    unique_email = f"{uuid.uuid4()}@example.com"
    person_payload = {
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": str(date(1990, 1, 1)),
        "email": unique_email,
        "phone_primary": "0123456789"
    }
    response = client.post("/persons/", json=person_payload)
    assert response.status_code == 200, response.text
    return response.json()

def test_person_address_association(create_address, create_person):
    address_id = create_address["address_id"]
    party_id = create_person["party_id"]

    # Initially, no associations
    pa_response = client.get("/party-addresses/")
    assert pa_response.status_code == 200
    assert pa_response.json() == []

    # Link Person (Party) to Address explicitly
    link_payload = {
        "party_id": party_id,
        "address_id": address_id
    }
    link_response = client.post("/party-addresses/", json=link_payload)
    assert link_response.status_code == 200, link_response.text

    # Verify PartyAddress link is created
    pa_response = client.get("/party-addresses/")
    assert pa_response.status_code == 200
    pa_records = pa_response.json()
    assert any(record["party_id"] == party_id and record["address_id"] == address_id for record in pa_records)