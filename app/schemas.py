from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from .models import EventStatus
import pytz

# Helper function to convert naive datetime to aware datetime


def make_aware(dt: datetime, timezone=pytz.UTC):
    if dt.tzinfo is None:
        return timezone.localize(dt)
    return dt


class AttendeeBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str


class AttendeeCreate(AttendeeBase):
    pass


class Attendee(AttendeeBase):
    attendee_id: int
    event_id: int
    check_in_status: bool

    class ConfigDict:
        from_attributes = True


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    role: str

    class Config:
        orm_mode = True


class EventBase(BaseModel):
    name: str
    description: str
    location: str
    max_attendees: int


class EventCreate(EventBase):
    start_time: datetime
    end_time: datetime

    def __init__(self, **data):
        super().__init__(**data)
        self.start_time = make_aware(self.start_time)
        self.end_time = make_aware(self.end_time)


class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    max_attendees: Optional[int] = None
    status: Optional[EventStatus] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.start_time:
            self.start_time = make_aware(self.start_time)
        if self.end_time:
            self.end_time = make_aware(self.end_time)


class Event(EventBase):
    event_id: int
    status: EventStatus
    attendees: List[Attendee] = []

    class ConfigDict:
        from_attributes = True
