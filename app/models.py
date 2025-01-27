from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from .database import Base
import enum


class EventStatus(str, enum.Enum):
    SCHEDULED = 'scheduled'
    ONGOING = 'ongoing'
    COMPLETED = 'completed'
    CANCELED = 'canceled'


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)


class Event(Base):
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String)
    max_attendees = Column(Integer)
    status = Column(Enum(EventStatus), default=EventStatus.SCHEDULED)

    attendees = relationship("Attendee", back_populates="event")


class Attendee(Base):
    __tablename__ = "attendees"

    attendee_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
    event_id = Column(Integer, ForeignKey("events.event_id"))
    check_in_status = Column(Boolean, default=False)

    event = relationship("Event", back_populates="attendees")
