import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from app.main import app
from app.database import Base, engine, get_db
from app.auth import create_access_token
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from app.models import Event, Attendee
from faker import Faker
import random

fake = Faker()


# Create an in-memory(Similar like memecache or redis) SQLite database
# TEST_DATABASE_URL = "sqlite:///:memory:"
TEST_DATABASE_URL = "sqlite:///test.db"
engine = create_engine(TEST_DATABASE_URL)

# Create all tables
Base.metadata.create_all(bind=engine)

# Create a configured "SessionLocal" class
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def test_db():
    # Create a new session for testing
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers():
    # Generate a valid auth token for testing
    access_token = create_access_token({"sub": "testuser"})
    return {"Authorization": f"Bearer {access_token}"}


def test_register_user(client):
    user_data = {
        "username": fake.name(),
        "password": "password"
    }

    # Send a POST request to create the event
    response = client.post("/register", json=user_data)

    # Assert that the response status code is 201 (Ok & Resource created)
    assert response.status_code == 200
    data = response.json()
    assert user_data["username"] == data["username"]


def test_create_event(client, auth_headers):
    # Define the event data
    event_data = {
        "name": "Test Event1",
        "description": "Test Description",
        "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "location": "Test Location",
        "max_attendees": 1
    }

    # Send a POST request to create the event
    response = client.post("/event", json=event_data, headers=auth_headers)

    # Assert that the response status code is 201 (Ok & Resource created)
    assert response.status_code == 201

    # Assert that the response data matches the event data
    response_data = response.json()
    assert response_data["name"] == event_data["name"]
    assert response_data["description"] == event_data["description"]
    assert response_data["location"] == event_data["location"]
    assert response_data["max_attendees"] == event_data["max_attendees"]


def test_update_event(client, auth_headers):
    # Create an event
    event_data = {
        "name": "Test Event",
        "description": "Test event description",
        "location": "Test Location",
        "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "max_attendees": 100
    }
    response = client.post("/event", json=event_data, headers=auth_headers)
    data = response.json()
    assert response.status_code == 201
    assert data["name"] == event_data["name"]
    assert data["description"] == event_data["description"]
    assert data["location"] == event_data["location"]
    assert data["max_attendees"] == event_data["max_attendees"]
    event_id = data["event_id"]

    # Update the event
    update_data = {"name": "Updated Test Event"}
    response = client.put(f"/event/{event_id}",
                          json=update_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Test Event"


def test_register_attendee(client, auth_headers):
    # Create an event
    event_data = {
        "name": "Test Event",
        "location": "Test Location",
        "description": "Test Description",
        "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "max_attendees": 100
    }
    response = client.post("/event", json=event_data, headers=auth_headers)
    assert response.status_code == 201
    event_id = response.json()["event_id"]

    # Register an attendee
    attendee_data = {
        "attendee_id": random.randint(1, 10),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "phone_number": fake.phone_number()
    }
    response = client.post(f"/event/{event_id}/attendees", json=attendee_data)
    assert response.status_code == 200
    assert response.json()["event_id"] == event_id

def test_checkin_attendee(client, auth_headers):
    # Create an event
    event_data = {
        "name": "Test Event",
        "location": "Test Location",
        "description": "Test Description",
        "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "max_attendees": 100
    }
    response = client.post("/event", json=event_data, headers=auth_headers)
    assert response.status_code == 201
    event_id = response.json()["event_id"]

    # Register an attendee
    attendee_data = {
        "attendee_id": random.randint(1, 10),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "phone_number": fake.phone_number()
    }
    response = client.post(f"/event/{event_id}/attendees", json=attendee_data, headers = auth_headers)
    assert response.status_code == 200
    attendee_id = response.json()["attendee_id"]

    # Check in the attendee
    response = client.put(f"/event/{event_id}/attendees/{attendee_id}/checkin", headers = auth_headers)
    assert response.status_code == 200
    assert response.json()["check_in_status"] == True


def test_bulk_checkin_attendees(client, auth_headers):
    # Create an event
    event_data = {
        "name": "Test Event",
        "location": "Test Location",
        "description": "Test Description",
        "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "max_attendees": 100
    }
    response = client.post("/event", json=event_data, headers=auth_headers)
    assert response.status_code == 201
    event_id = response.json()["event_id"]

    # Register attendees
    attendees_data = [
        {
            "attendee_id": 5,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone_number": fake.phone_number()
        },
        {
            "attendee_id": 6,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone_number": fake.phone_number()
        }
    ]
    for attendee_data in attendees_data:
        response = client.post(
            f"/event/{event_id}/attendees", json=attendee_data, headers=auth_headers)
        assert response.status_code == 200

    # Bulk check-in attendees
    csv_content = "attendee_id\n{}\n{}\n".format(
        attendees_data[0]["attendee_id"], attendees_data[1]["attendee_id"])

    response = client.post(f"/event/{event_id}/attendees/bulk-checkin",
                        files={"file": ("bulk_checkin.csv", csv_content, "text/csv")}, headers=auth_headers)
    assert response.status_code == 200  # Ensure bulk check-in is successful


def test_list_events(client, auth_headers, test_db: Session):
    # Create events
    event_data1 = {
        "name": "Test Event1",
        "location": "Test Location",
        "description": "Test Description",
        "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "max_attendees": 100
    }
    event_data2 = {
        "name": "Test Event2",
        "location": "Test Location",
        "description": "Test Description",
        "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "max_attendees": 100
    }
    test_db.query(Event).delete()
    test_db.commit()
    response_event1 = client.post("/event", json=event_data1, headers = auth_headers)
    response_event2 = client.post("/event", json=event_data2, headers = auth_headers)
    assert response_event1.status_code == 201
    assert response_event2.status_code == 201

    # List events
    response = client.get("/events", headers = auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_attendees(client, auth_headers, test_db:Session):
    # Create an event
    event_data = {
        "name": "Test Event",
        "location": "Test Location",
        "description": "Test Description",
        "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "max_attendees": 100
    }
    response = client.post("/event", json=event_data, headers=auth_headers)
    assert response.status_code == 201
    event_id = response.json()["event_id"]

    # Register attendees
    attendees_data = [
        {
            "attendee_id": random.randint(0, 10),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone_number": fake.phone_number()
        },
        {
            "attendee_id": random.randint(0, 10),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone_number": fake.phone_number()
        }
    ]
    test_db.query(Attendee).delete()
    test_db.commit()
    for attendee_data in attendees_data:
        response = client.post(
            f"/event/{event_id}/attendees", json=attendee_data, headers=auth_headers)
        assert response.status_code == 200

    # List attendees
    response = client.get(f"/event/{event_id}/attendees", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


if __name__ == "__main__":
    pytest.main()
