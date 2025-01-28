from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import csv
import io
from .database import Base
from . import crud, schemas, auth, models
from .database import engine, get_db
from datetime import datetime, timezone

app = FastAPI(title="Event Management API")

# Create the database tables
Base.metadata.create_all(bind=engine)

# Automatically update event status to 'completed' if end_time has passed
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    db = next(get_db())
    events = db.query(models.Event).filter(models.Event.end_time < datetime.now(timezone.utc)).all()
    for event in events:
        event.status = "completed"
        db.commit()
        db.refresh(event)
    yield
    # Shutdown code (if needed)

app = FastAPI(lifespan=lifespan)

@app.post("/register", response_model=schemas.Register)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

# Authentication endpoints
@app.post("/token", include_in_schema=False)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/event", response_model=schemas.Event, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: schemas.EventCreate,
    db: Session = Depends(get_db),
    token: dict = Depends(auth.verify_token)
):
    return crud.create_event(db=db, event=event)

@app.put("/event/{event_id}", response_model=schemas.Event)
async def update_event(
    event_id: int,
    event_update: schemas.EventUpdate,
    db: Session = Depends(get_db),
    token: dict = Depends(auth.verify_token)
):
    event = crud.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    for key, value in event_update.model_dump(exclude_unset=True).items():
        setattr(event, key, value)
    
    crud.update_event_status(db, event)
    db.commit()
    db.refresh(event)
    return event

@app.post("/event/{event_id}/attendees", response_model=schemas.Attendee)
async def register_attendee(
    attendee: schemas.Attendee,
    db: Session = Depends(get_db),
    token: dict = Depends(auth.verify_token)
):
    event = crud.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if len(event.attendees) >= event.max_attendees:
        raise HTTPException(status_code=400, detail="Max attendees limit reached")
    
    return crud.register_attendee(db, event_id, attendee)

@app.put("/event/{event_id}/attendees/{attendee_id}/checkin", response_model=schemas.Attendee)
async def checkin_attendee(
    event_id: int,
    attendee_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(auth.verify_token)
):
    attendee = db.query(models.Attendee).filter(
        models.Attendee.event_id == event_id,
        models.Attendee.attendee_id == attendee_id
    ).first()

    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")

    attendee.check_in_status = True
    db.commit()
    db.refresh(attendee)
    return attendee

@app.post("/event/{event_id}/attendees/bulk-checkin", response_model=List[schemas.Attendee])
async def bulk_checkin_attendees(
    event_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: dict = Depends(auth.verify_token)
):
    content = await file.read()
    csv_reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    attendees = []
    for row in csv_reader:
        attendee_id = int(row["attendee_id"])
        attendee = db.query(models.Attendee).filter(
            models.Attendee.event_id == event_id,
            models.Attendee.attendee_id == attendee_id
        ).first()
        if attendee:
            attendee.check_in_status = True
            db.commit()
            db.refresh(attendee)
            attendees.append(attendee)
    return attendees

# Get list of the events
@app.get("/events", response_model=List[schemas.Event])
async def list_events(
    eventList: schemas.EventList,
    db: Session = Depends(get_db)
):
    query = db.query(models.Event)

    if status:
        query = query.filter(models.Event.status == status)
    if eventList.location:
        query = query.filter(models.Event.location == eventList.location)
    if eventList.date:
        query = query.filter(models.Event.start_time <=
                             eventList.date, models.Event.end_time >= eventList.date)

    events = query.all()
    return events

@app.get("/event/{event_id}/attendees", response_model=List[schemas.Attendee])
async def list_attendees(
    attendeesCheckIn: schemas.AttendeesCheckIn,
    db: Session = Depends(get_db)
):
    query = db.query(models.Attendee).filter(
        models.Attendee.event_id == attendeesCheckIn.event_id)

    if attendeesCheckIn.check_in_status is not None:
        query = query.filter(
            models.Attendee.check_in_status == attendeesCheckIn.check_in_status)

    attendees = query.all()
    return attendees