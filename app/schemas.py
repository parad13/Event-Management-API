from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from .models import EventStatus

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

class EventBase(BaseModel):
    name: str
    description: str
    start_time: datetime
    end_time: datetime
    location: str
    max_attendees: int

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    max_attendees: Optional[int] = None
    status: Optional[EventStatus] = None

class Event(EventBase):
    event_id: int
    status: EventStatus
    attendees: List[Attendee] = []

    class ConfigDict:
        from_attributes = True
