from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import csv
from .database import Base
import io
from app.auth import verify_password, create_access_token


from . import crud, models, schemas, auth
from .database import engine, get_db

app = FastAPI(title="Event Management API")

# Create the database tables
Base.metadata.create_all(bind=engine)


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

# Authentication endpoints


@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Protected endpoints


@app.post("/events/", response_model=schemas.Event, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: schemas.EventCreate,
    db: Session = Depends(get_db),
    token: dict = Depends(auth.verify_token)
):
    return crud.create_event(db=db, event=event)


@app.get("/events/{event_id}", response_model=schemas.Event)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = crud.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.post("/events/{event_id}/bulk-checkin")
async def bulk_checkin(
    event_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: dict = Depends(auth.verify_token)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )

    content = await file.read()
    try:
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        return crud.bulk_checkin(db=db, event_id=event_id, csv_data=csv_reader)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing CSV file: {str(e)}"
        )
