"""
Pydantic models for request/response validation.
Defines data structures for API endpoints.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class AddressResponse(BaseModel):
    """Response containing geocoded address coordinates."""

    address: str
    latitude: float
    longitude: float


class AddressRequest(BaseModel):
    """Request to geocode an address or get schedule."""

    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SweepBlock(BaseModel):
    """A single street sweeping block."""

    corridor: str
    limits: str
    blockside: str
    weekday: str
    fullname: str
    fromhour: int
    tohour: int
    week1: bool
    week2: bool
    week3: bool
    week4: bool
    week5: bool
    distance_meters: Optional[float] = None


class SweepScheduleResponse(BaseModel):
    """Response containing sweeping schedule information."""

    address: str
    latitude: float
    longitude: float
    schedule: List[SweepBlock]


class SavedLocation(BaseModel):
    """A saved parking location."""

    id: str
    address: str
    latitude: float
    longitude: str
    street_segment_id: str
    created_at: datetime


class SubscriptionRequest(BaseModel):
    """Request to subscribe to notifications."""

    address: str
    latitude: float
    longitude: float
    notification_hours_before: int = Field(default=12, ge=1, le=24)
    notification_method: str = Field(default="push")  # push, sms, email


class SubscriptionResponse(BaseModel):
    """Response after creating a subscription."""

    success: bool
    message: str
    subscription_id: str


class NotificationPreferences(BaseModel):
    """User notification preferences."""

    hours_before: int = Field(default=12, ge=1, le=24)
    methods: List[str] = ["push"]  # push, sms, email
    quiet_hours_start: Optional[int] = None  # 0-23
    quiet_hours_end: Optional[int] = None  # 0-23
