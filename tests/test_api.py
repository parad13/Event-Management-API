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

# Setup the test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI TestClient
client = TestClient(app)

@pytest.fixture(autouse=True)
def test_db():
    # Create all tables in the test database before each test
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)  # Clean up after the tests

@pytest.fixture
def db_session():
    # Provide a session to interact with the database
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def auth_headers():
    # Generate a valid auth token for testing
    access_token = create_access_token({"sub": "testuser"})
    return {"Authorization": f"Bearer {access_token}"}

def test_create_event(auth_headers, db_session):
    # Create mock event data
    event_data = {
        "name": "Test Event",
        "description": "A test event for unit testing.",
        "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "location": "Test Location",
        "max_attendees": 10
    }


# def test_registration_limit(auth_headers, db_session):
#     # Create event with a maximum of 1 attendee
#     event_data = {
#         "name": "Test Event",
#         "description": "Test Description",
#         "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
#         "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
#         "location": "Test Location",
#         "max_attendees": 1
#     }
    
#     # Create event
#     event_response = client.post("/event", json=event_data, headers=auth_headers)
#     assert event_response.status_code == 201  # Created
#     event_id = event_response.json()["event_id"]
    
#     # Register first attendee
#     attendee1 = {
#         "first_name": "John",
#         "last_name": "Doe",
#         "email": "john@example.com",
#         "phone_number": "1234567890"
#     }
#     response1 = client.post(
#         f"/event/{event_id}/attendees",
#         json=attendee1,
#         headers=auth_headers
#     )
#     assert response1.status_code == 201  # Created
    
#     # Try to register second attendee (should fail due to the limit)
#     attendee2 = {
#         "first_name": "Jane",
#         "last_name": "Doe",
#         "email": "jane@example.com",
#         "phone_number": "0987654321"
#     }
#     response2 = client.post(
#         f"/event/{event_id}/attendees",
#         json=attendee2,
#         headers=auth_headers
#     )
#     assert response2.status_code == 400  # Bad Request
#     assert "Max attendees limit reached" in response2.json()["detail"]

# def test_automatic_status_update(auth_headers, db_session):
#     event_data = {
#         "name": "Past Event",
#         "description": "Test Description",
#         "start_time": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
#         "end_time": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
#         "location": "Test Location",
#         "max_attendees": 10
#     }
    
#     response = client.post("/event", json=event_data, headers=auth_headers)
#     assert response.status_code == 201  # Created
#     event_id = response.json()["event_id"]
    
#     get_response = client.get(f"/event/{event_id}", headers=auth_headers)
#     assert get_response.status_code == 200  # OK
#     assert get_response.json()["status"] == "completed"

# def test_check_in_attendee(auth_headers, db_session):
#     # Create event
#     event_data = {
#         "name": "Check-in Test Event",
#         "description": "Test Description",
#         "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
#         "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
#         "location": "Test Location",
#         "max_attendees": 10
#     }
    
#     event_response = client.post("/event", json=event_data, headers=auth_headers)
#     event_id = event_response.json()["event_id"]
    
#     # Register attendee
#     attendee_data = {
#         "first_name": "Test",
#         "last_name": "User",
#         "email": "test@example.com",
#         "phone_number": "1234567890"
#     }
    
#     register_response = client.post(
#         f"/event/{event_id}/attendees", 
#         json=attendee_data,
#         headers=auth_headers
#     )
#     attendee = register_response.json()
    
#     # Check-in attendee
#     checkin_response = client.put(
#         f"/event/{event_id}/attendees/{attendee['attendee_id']}/checkin",
#         headers=auth_headers
#     )
#     assert checkin_response.status_code == 200  # OK
#     assert checkin_response.json()["check_in_status"] is True

# def test_bulk_checkin_attendees(auth_headers, db_session):
#     # Create event
#     event_data = {
#         "name": "Bulk Check-in Test Event",
#         "description": "Test Description",
#         "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
#         "end_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
#         "location": "Test Location",
#         "max_attendees": 10
#     }
    
#     event_response = client.post("/event", json=event_data, headers=auth_headers)
#     event_id = event_response.json()["event_id"]
    
#     # Register attendees
#     attendees_data = [
#         {"first_name": "John", "last_name": "Doe", "email": "john@example.com", "phone_number": "1234567890"},
#         {"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com", "phone_number": "0987654321"}
#     ]
    
#     for attendee_data in attendees_data:
#         client.post(f"/event/{event_id}/attendees", json=attendee_data, headers=auth_headers)
    
#     # Create CSV for bulk check-in
#     csv_content = "attendee_id\n1\n2\n"
#     file = io.BytesIO(csv_content.encode("utf-8"))
    
#     # Bulk check-in attendees
#     response = client.post(
#         f"/event/{event_id}/attendees/bulk-checkin",
#         files={"file": ("attendees.csv", file, "text/csv")},
#         headers=auth_headers
#     )
#     assert response.status_code == 200  # OK
#     checked_in_attendees = response.json()
#     assert len(checked_in_attendees) == 2
#     assert all(attendee["check_in_status"] for attendee in checked_in_attendees)
