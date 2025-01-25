import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from app.main import app
from app.database import Base, engine
from app.auth import create_access_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_headers():
    access_token = create_access_token({"sub": "testuser"})
    return {"Authorization": f"Bearer {access_token}"}

def test_registration_limit(auth_headers):
    # Create event with max 1 attendee
    event_data = {
        "name": "Test Event",
        "description": "Test Description",
        "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "location": "Test Location",
        "max_attendees": 1
    }
    
    # Create event
    event_response = client.post("/events/", json=event_data, headers=auth_headers)
    assert event_response.status_code == 201  # Created
    event_id = event_response.json()["event_id"]
    
    # Register first attendee
    attendee1 = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone_number": "1234567890"
    }
    response1 = client.post(
        f"/events/{event_id}/register",
        json=attendee1,
        headers=auth_headers
    )
    assert response1.status_code == 201  # Created
    
    # Try to register second attendee
    attendee2 = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "phone_number": "0987654321"
    }
    response2 = client.post(
        f"/events/{event_id}/register",
        json=attendee2,
        headers=auth_headers
    )
    assert response2.status_code == 400  # Bad Request
    assert "fully booked" in response2.json()["detail"]

def test_automatic_status_update(auth_headers):
    event_data = {
        "name": "Past Event",
        "description": "Test Description",
        "start_time": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
        "end_time": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "location": "Test Location",
        "max_attendees": 10
    }
    
    response = client.post("/events/", json=event_data, headers=auth_headers)
    assert response.status_code == 201  # Created
    event_id = response.json()["event_id"]
    
    get_response = client.get(f"/events/{event_id}", headers=auth_headers)
    assert get_response.status_code == 200  # OK
    assert get_response.json()["status"] == "completed"

def test_check_in_attendee(auth_headers):
    # Create event
    event_data = {
        "name": "Check-in Test Event",
        "description": "Test Description",
        "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "location": "Test Location",
        "max_attendees": 10
    }
    
    event_response = client.post("/events/", json=event_data, headers=auth_headers)
    event_id = event_response.json()["event_id"]
    
    # Register attendee
    attendee_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone_number": "1234567890"
    }
    
    register_response = client.post(
        f"/events/{event_id}/register", 
        json=attendee_data,
        headers=auth_headers
    )
    attendee = register_response.json()
    
    # Check in attendee
    checkin_response = client.patch(
        f"/events/{event_id}/attendees/{attendee['attendee_id']}/check-in",
        headers=auth_headers
    )
    assert checkin_response.status_code == 200
