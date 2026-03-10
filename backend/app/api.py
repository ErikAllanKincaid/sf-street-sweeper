"""
API routes for the SF Street Sweeper backend.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.sf_data import SFSweepingService
from app.services.geocoding import GeocodingService
from app.models import (
    AddressRequest,
    SweepScheduleResponse,
    SubscriptionRequest,
    SubscriptionResponse,
)

router = APIRouter()
sweeping_service = SFSweepingService()
geocoding_service = GeocodingService()


@router.get("/")
async def root():
    return {"status": "ok"}


@router.post("/geocode")
async def geocode_address(request: AddressRequest):
    result = await geocoding_service.geocode(request.address)
    return result


@router.post("/sweep")
async def get_sweep_schedule(request: AddressRequest):
    """Get sweeping schedule for address."""
    try:
        if not request.address:
            raise HTTPException(status_code=400, detail="Address is required")

        coords = await geocoding_service.geocode(request.address)

        # Get sweeps within 150m
        all_sweeps = await sweeping_service.find_all_sweeps(
            coords["latitude"],
            coords["longitude"],
            max_distance=150,
            limit=50,
        )

        # Filter by distance (service sets distance_meters key)
        all_sweeps = [
            s for s in all_sweeps if s.get("distance_meters", float("inf")) <= 150
        ]

        # Sort by distance, limit to 10
        all_sweeps.sort(key=lambda x: x.get("distance_meters", float("inf")))
        all_sweeps = all_sweeps[:10]

        return {
            "address": coords["address"],
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "schedule": all_sweeps,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscribe")
async def subscribe(request: SubscriptionRequest):
    return SubscriptionResponse(success=True, message="OK", subscription_id="demo")
