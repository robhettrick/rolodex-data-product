import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine
import uuid
import pytest
import redis

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

@pytest.fixture(autouse=True)
def clear_redis():
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    redis_client.flushdb()


def create_person(first_name, last_name, email):
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone_primary": "0123456789"
    }
    response = client.post("/persons/", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    return result["data"]


def create_organisation(name, org_type):
    payload = {
        "organisation_name": name,
        "organisation_type": org_type,
        "email": f"info@{uuid.uuid4().hex[:6]}.com",
        "phone_primary": "0987654321"
    }
    response = client.post("/organisations/", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    return result["data"]


def create_address(line1):
    payload = {
        "address_line_1": line1,
        "city": "Chipping Norton",
        "postal_code": "OX7 3PE",
        "country": "UK",
        "address_type": "Business"
    }
    response = client.post("/addresses/", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    return result["data"]


def link_party_address(party_id, address_id):
    payload = {"party_id": party_id, "address_id": address_id}
    response = client.post("/party-addresses/", json=payload)
    assert response.status_code == 200, response.text


def create_external_identifier(party_id, system_name):
    payload = {
        "party_id": party_id,
        "system_name": system_name,
        "external_id": uuid.uuid4().hex[:8]
    }
    response = client.post("/external-identifiers/", json=payload)
    assert response.status_code == 200, response.text


def create_relationship(from_id, to_id, relationship_type):
    payload = {
        "from_party_id": from_id,
        "to_party_id": to_id,
        "relationship_type": relationship_type
    }
    response = client.post("/party-relationships/", json=payload)
    assert response.status_code == 200, response.text


def test_clarksons_farm_scenario():
    # Create organisations
    diddly_squat = create_organisation("Diddly Squat Farm", "Farm")
    coop = create_organisation("Local Farmers Co-op", "Farm Co-op")

    # Create addresses and link
    diddly_address = create_address("Diddly Squat Farm")
    coop_address = create_address("1 Farm Road")

    link_party_address(diddly_squat["party_id"], diddly_address["address_id"])
    link_party_address(coop["party_id"], coop_address["address_id"])

    # Create people
    jeremy = create_person("Jeremy", "Clarkson", "jeremy@farm.com")
    kaleb = create_person("Kaleb", "Cooper", "kaleb@farm.com")
    charlie = create_person("Charlie", "Ireland", "charlie@advisor.com")
    lisa = create_person("Lisa", "Hogan", "lisa@farmshop.com")
    # Additional characters
    harriet = create_person("Harriet", "Cowan", "harriet@farm.com")
    gerald = create_person("Gerald", "Cooper", "gerald@farmworker.com")

    # Link people to addresses
    link_party_address(jeremy["party_id"], diddly_address["address_id"])
    link_party_address(kaleb["party_id"], diddly_address["address_id"])
    link_party_address(charlie["party_id"], coop_address["address_id"])
    link_party_address(lisa["party_id"], diddly_address["address_id"])

    # Create legacy identifiers
    for party in [jeremy, kaleb, charlie, lisa]:
        create_external_identifier(party["party_id"], "SAM")

    for org in [diddly_squat, coop]:
        create_external_identifier(org["party_id"], "Eldorado")

    # Define relationships clearly
    create_relationship(jeremy["party_id"], diddly_squat["party_id"], "Owner")
    create_relationship(kaleb["party_id"], diddly_squat["party_id"], "Farm Manager")
    create_relationship(charlie["party_id"], diddly_squat["party_id"], "Advisor")
    create_relationship(lisa["party_id"], diddly_squat["party_id"], "Farm Shop Manager")
    create_relationship(jeremy["party_id"], lisa["party_id"], "Married")
    create_relationship(gerald["party_id"], diddly_squat["party_id"], "Farm Worker")
    create_relationship(harriet["party_id"], diddly_squat["party_id"], "Interim Farm Manager")
    create_relationship(diddly_squat["party_id"], coop["party_id"], "Member")
    create_relationship(gerald["party_id"], kaleb["party_id"], "Cousin")

    # Verify relationships
    rel_response = client.get("/party-relationships/")
    assert rel_response.status_code == 200
    wrappers = rel_response.json()
    relationships = [entry["data"] for entry in wrappers]
    assert len(relationships) == 9

    expected_relations = [
        ("Owner", jeremy["party_id"], diddly_squat["party_id"]),
        ("Farm Manager", kaleb["party_id"], diddly_squat["party_id"]),
        ("Advisor", charlie["party_id"], diddly_squat["party_id"]),
        ("Farm Shop Manager", lisa["party_id"], diddly_squat["party_id"]),
        ("Member", diddly_squat["party_id"], coop["party_id"]),
        ("Farm Worker", gerald["party_id"], diddly_squat["party_id"]),
        ("Married", jeremy["party_id"], lisa["party_id"]),
    ]

    for r_type, from_id, to_id in expected_relations:
        assert any(
            rel["relationship_type"] == r_type and
            rel["from_party_id"] == from_id and
            rel["to_party_id"] == to_id
            for rel in relationships
        )