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

        # Extract street name from geocoded address (e.g., "Clipper Street" from "301, Clipper Street, ...")
        address_parts = coords["address"].split(",")
        street_name = address_parts[1].strip() if len(address_parts) > 1 else ""
        # Normalize street name (remove "St", "Street", etc. for matching)
        street_base = (
            street_name.lower().replace("street", "").replace("st", "").strip()
        )

        # Get sweeps within 150m
        all_sweeps = await sweeping_service.find_all_sweeps(
            coords["latitude"],
            coords["longitude"],
            max_distance=150,
            limit=100,
        )

        # Filter by distance
        all_sweeps = [
            s for s in all_sweeps if s.get("distance_meters", float("inf")) <= 150
        ]

        # Filter to ONLY the street the address is on (not nearby streets)
        # Match by street name in the corridor
        matching_street = [
            s
            for s in all_sweeps
            if street_base
            in s.get("corridor", "")
            .lower()
            .replace("st", "")
            .replace("street", "")
            .replace(" ", "")
        ]

        # Use only matching street if found, otherwise fall back to closest
        if matching_street:
            all_sweeps = matching_street

        # Sort by distance and take ONLY the closest segment
        all_sweeps.sort(key=lambda x: x.get("distance_meters", float("inf")))

        # Return single closest segment only
        if all_sweeps:
            all_sweeps = all_sweeps[:1]

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
