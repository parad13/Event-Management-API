from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from . import models, schemas

def update_event_status(db: Session, event: models.Event):
    current_time = datetime.now(timezone.utc)
    if event.end_time < current_time and event.status != models.EventStatus.COMPLETED:
        event.status = models.EventStatus.COMPLETED
        db.commit()



def create_event(db: Session, event: schemas.EventCreate):
    db_event = models.Event(**event.model_dump())
    if db_event.end_time < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event end time cannot be in the past"
        )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_event(db: Session, event_id: int):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if event:
        update_event_status(db, event)
    return event

def register_attendee(db: Session, event_id: int, attendee: schemas.AttendeeCreate):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    update_event_status(db, event)
    if event.status == models.EventStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot register for completed event"
        )
    
    attendee_count = db.query(models.Attendee).filter(
        models.Attendee.event_id == event_id
    ).count()
    
    if attendee_count >= event.max_attendees:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event has reached maximum capacity"
        )
    
    db_attendee = models.Attendee(**attendee.model_dump(), event_id=event_id)
    db.add(db_attendee)
    db.commit()
    db.refresh(db_attendee)
    return db_attendee

def bulk_checkin(db: Session, event_id: int, csv_data: List[dict]):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
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
                results["errors"].append(f"Attendee not found: {row.get('email')}")
                
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Error processing {row.get('email')}: {str(e)}")
    
    db.commit()
    return results
