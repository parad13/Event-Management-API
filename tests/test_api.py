import io
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from app.main import app
from app.database import Base, engine, get_db
from app.auth import create_access_token
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Event, Attendee
from faker import Faker

fake = Faker()

# Create an in-memory(Similar like memecache or redis) SQLite database
# TEST_DATABASE_URL = "sqlite:///:memory:"
TEST_DATABASE_URL = "sqlite:///test.db"
engine = create_engine(TEST_DATABASE_URL)

# Create all tables
Base.metadata.create_all(bind=engine)

# Create a configured "SessionLocal" class
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    import pdb; pdb.set_trace()
    assert user_data["username"] == data.username


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
    print("Response data", response_data)
    assert response_data["name"] == event_data["name"]
    assert response_data["description"] == event_data["description"]
    assert response_data["location"] == event_data["location"]
    assert response_data["max_attendees"] == event_data["max_attendees"]

def test_update_event(client, auth_headers):
    # Create an event
    event_data = {"name": "Test Event", "location": "Test Location", "start_time": "2025-01-01T10:00:00Z", "end_time": "2025-01-01T12:00:00Z", "max_attendees": 100}
    response = client.post("/event", json=event_data)
    assert response.status_code == 201
    event_id = response.json()["id"]

    # Update the event
    update_data = {"name": "Updated Test Event"}
    response = client.put(f"/event/{event_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Test Event"

def test_register_attendee(client, auth_headers):
    # Create an event
    event_data = {"name": "Test Event", "location": "Test Location", "start_time": "2025-01-01T10:00:00Z", "end_time": "2025-01-01T12:00:00Z", "max_attendees": 100}
    response = client.post("/event", json=event_data)
    assert response.status_code == 201
    event_id = response.json()["id"]

    # Register an attendee
    attendee_data = {"name": "Test Attendee", "email": "test@example.com"}
    response = client.post(f"/event/{event_id}/attendees", json=attendee_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Attendee"

def test_checkin_attendee(client, auth_headers):
    # Create an event
    event_data = {"name": "Test Event", "location": "Test Location", "start_time": "2025-01-01T10:00:00Z", "end_time": "2025-01-01T12:00:00Z", "max_attendees": 100}
    response = client.post("/event", json=event_data)
    assert response.status_code == 201
    event_id = response.json()["id"]

    # Register an attendee
    attendee_data = {"name": "Test Attendee", "email": "test@example.com"}
    response = client.post(f"/event/{event_id}/attendees", json=attendee_data)
    assert response.status_code == 200
    attendee_id = response.json()["id"]

    # Check in the attendee
    response = client.put(f"/event/{event_id}/attendees/{attendee_id}/checkin")
    assert response.status_code == 200
    assert response.json()["check_in_status"] == True

def test_bulk_checkin_attendees(client, auth_headers):
    # Create an event
    event_data = {"name": "Test Event", "location": "Test Location", "start_time": "2025-01-01T10:00:00Z", "end_time": "2025-01-01T12:00:00Z", "max_attendees": 100}
    response = client.post("/event", json=event_data)
    assert response.status_code == 201
    event_id = response.json()["id"]

    # Register attendees
    attendees_data = [
        {"name": "Attendee 1", "email": "attendee1@example.com"},
        {"name": "Attendee 2", "email": "attendee2@example.com"}
    ]
    for attendee_data in attendees_data:
        response = client.post(f"/event/{event_id}/attendees", json=attendee_data)
        assert response.status_code == 200

    # Bulk check in attendees
    csv_content = "attendee_id\n1\n2\n"
    response = client.post(f"/event/{event_id}/attendees/bulk-checkin", files={"file": ("bulk_checkin.csv", csv_content, "text/csv")})
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert all(attendee["check_in_status"] == True for attendee in response.json())

def test_list_events(client, auth_headers):
    # Create events
    event_data1 = {"name": "Event 1", "location": "Location 1", "start_time": "2025-01-01T10:00:00Z", "end_time": "2025-01-01T12:00:00Z", "max_attendees": 100}
    event_data2 = {"name": "Event 2", "location": "Location 2", "start_time": "2025-01-02T10:00:00Z", "end_time": "2025-01-02T12:00:00Z", "max_attendees": 100}
    client.post("/event", json=event_data1)
    client.post("/event", json=event_data2)

    # List events
    response = client.get("/events")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_list_attendees(client, auth_headers):
    # Create an event
    event_data = {"name": "Test Event", "location": "Test Location", "start_time": "2025-01-01T10:00:00Z", "end_time": "2025-01-01T12:00:00Z", "max_attendees": 100}
    response = client.post("/event", json=event_data)
    assert response.status_code == 201
    event_id = response.json()["id"]

    # Register attendees
    attendees_data = [
        {"name": "Attendee 1", "email": "attendee1@example.com"},
        {"name": "Attendee 2", "email": "attendee2@example.com"}
    ]
    for attendee_data in attendees_data:
        response = client.post(f"/event/{event_id}/attendees", json=attendee_data)
        assert response.status_code == 200

    # List attendees
    response = client.get(f"/event/{event_id}/attendees")
    assert response.status_code == 200
    assert len(response.json()) == 2

