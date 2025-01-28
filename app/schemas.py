from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional, List
from .models import EventStatus
import pytz

from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Helper function to convert naive datetime to aware datetime


def make_aware(dt: datetime, timezone=pytz.UTC):
    if dt.tzinfo is None:
        return timezone.localize(dt)
    return dt


class AttendeeBase(BaseModel):
    attendee_id:  Optional[int] = None 
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str


class Attendee(AttendeeBase):
    check_in_status: bool
    model_config = ConfigDict(from_attributes=True)


class AttendeeCreate(AttendeeBase):
    pass  # No additional fields required on creation


class AttendeesCheckIn(BaseModel):
    event_id: int
    check_in_status: bool


class AttendeeResponse(AttendeesCheckIn):

    class ConfigDict:
        from_attributes = True


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class Register(UserBase):
    id: int
    role: str

    class ConfigDict:
        from_attributes = True


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

    class ConfigDict:
        from_attributes = True


class EventList(BaseModel):
    status: Optional[EventStatus] = None,
    location: Optional[str] = None,
    date: Optional[datetime] = None,
