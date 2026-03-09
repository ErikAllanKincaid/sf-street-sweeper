"""
API routes for the SF Street Sweeper backend.
Defines endpoints for schedule lookup, geocoding, and subscriptions.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.sf_data import SFSweepingService
from app.services.geocoding import GeocodingService
from app.models import (
    AddressRequest,
    AddressResponse,
    SweepScheduleResponse,
    SavedLocation,
    SubscriptionRequest,
    SubscriptionResponse,
)

router = APIRouter()

# Service instances - in production these would be dependency-injected
sweeping_service = SFSweepingService()
geocoding_service = GeocodingService()


@router.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "SF Street Sweeper API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@router.post("/geocode", response_model=AddressResponse)
async def geocode_address(request: AddressRequest):
    """
    Geocode an address to coordinates.

    Takes a street address and returns latitude/longitude.
    Uses Nominatim (OpenStreetMap) for geocoding.
    """
    try:
        result = await geocoding_service.geocode(request.address)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sweep", response_model=SweepScheduleResponse)
async def get_sweep_schedule(request: AddressRequest):
    """
    Get the sweeping schedule for a given address.

    Takes an address, geocodes it, finds the nearest sweeping route,
    and returns the schedule information.
    """
    try:
        if not request.address:
            raise HTTPException(status_code=400, detail="Address is required")

        # Geocode the address
        coords = await geocoding_service.geocode(request.address)

        # Find nearest sweeping route
        sweep_info = await sweeping_service.find_nearest_sweep(
            coords["latitude"],
            coords["longitude"],
        )

        if not sweep_info:
            raise HTTPException(
                status_code=404, detail="No sweeping schedule found near this location"
            )

        # Format response to match SweepScheduleResponse
        return {
            "address": coords["address"],
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "schedule": [sweep_info],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe_to_notifications(request: SubscriptionRequest):
    """
    Subscribe to notifications for a parking location.

    Saves the location and notification preferences.
    In production, this would store in a database and set up push notifications.
    """
    # TODO: Implement database storage
    # TODO: Implement push notification subscription (FCM)

    return SubscriptionResponse(
        success=True,
        message="Subscription created (demo mode)",
        subscription_id="demo-123",
    )


@router.get("/schedule/{subscription_id}")
async def get_subscription_schedule(subscription_id: str):
    """
    Get the schedule for a saved subscription.
    """
    # TODO: Fetch from database
    return {
        "subscription_id": subscription_id,
        "next_sweep": "Tuesday, March 10, 2026",
        "sweep_time": "5:00 AM - 6:00 AM",
    }
