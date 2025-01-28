from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List
from . import models, schemas
from .auth import get_password_hash
import pytz
from datetime import datetime
import pytz
from sqlalchemy.orm import Session
from fastapi import HTTPException

# Helper function to convert naive datetime to aware datetime
def make_aware(dt: datetime, timezone=pytz.UTC):
    if dt.tzinfo is None:
        return timezone.localize(dt)
    return dt


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username,
                          hashed_password=hashed_password, role="user")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_event_status(db: Session, event_id: int):
    # Fetch the event by ID
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")  # Handle missing event

    if event.end_time is None:
        raise HTTPException(status_code=500, detail="Event does not have an 'end_time' set")

    current_time = datetime.now(pytz.UTC)
    
    # Ensure `event.end_time` is timezone-aware before comparison
    event_end_time = event.end_time
    if not event_end_time.tzinfo:  # Convert to aware if naive
        event_end_time = make_aware(event_end_time)

    if event_end_time < current_time and event.status != models.EventStatus.COMPLETED:
        event.status = models.EventStatus.COMPLETED
        db.commit()
        db.refresh(event)  # Ensure changes are reflected

    return event

def create_event(db: Session, event: schemas.EventCreate):
    db_event = models.Event(**event.model_dump())
    event_end_time = make_aware(db_event.end_time)
    if event_end_time < datetime.now(pytz.UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event end time cannot be in the past"
        )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_event(db: Session, event_id: int):
    return db.query(models.Event).filter(models.Event.event_id == event_id).first()

def register_attendee(db: Session, event_id: int, attendee_data: schemas.AttendeeCreate):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if len(event.attendees) >= event.max_attendees:
        raise HTTPException(status_code=400, detail="Max attendees limit reached")

    # 🔹 Check if the attendee already exists
    existing_attendee = db.query(models.Attendee).filter_by(email=attendee_data.email, event_id=event_id).first()
    if existing_attendee:
        raise HTTPException(status_code=400, detail="Attendee with this email is already registered for this event")

    new_attendee = models.Attendee(
        first_name=attendee_data.first_name,
        last_name=attendee_data.last_name,
        email=attendee_data.email,
        phone_number=attendee_data.phone_number,
        event_id=event_id,
        check_in_status=False
    )

    try:
        db.add(new_attendee)
        db.commit()
        db.refresh(new_attendee)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Database Integrity Error: Possible duplicate entry")

    return new_attendee

def get_attendee_count(db: Session, event_id: int) -> int:
    return db.query(models.Attendee).filter(models.Attendee.event_id == event_id).count()

def bulk_checkin(db: Session, event_id: int, csv_data: List[dict]):
    event = db.query(models.Event).filter(
        models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    results = {"success": 0, "failed": 0, "errors": []}

    for row in csv_data:
        try:
            attendee = db.query(models.Attendee).filter(
                models.Attendee.event_id == event_id,
                models.Attendee.email == row.get('email')
            ).first()

            if attendee:
                attendee.check_in_status = True
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(
                    f"Attendee not found: {row.get('email')}")

        except Exception as e:
            results["failed"] += 1
            results["errors"].append(
                f"Error processing {row.get('email')}: {str(e)}")

    db.commit()
    return results
