"""
API routes for the SF Street Sweeper backend.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.sf_data import SFSweepingService
from app.services.geocoding import GeocodingService
from app.services.calendar import generate_calendar_url, get_sweep_dates
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

        # Extract address number for auto side detection
        address_number = None
        try:
            # First part is usually the street number (e.g., "301" from "301, Clipper Street, ...")
            address_number = int(address_parts[0].strip().split()[0])
        except (ValueError, IndexError):
            pass

        # Normalize street name (remove "St", "Street", etc. for matching)
        street_base = (
            street_name.lower().replace("street", "").replace("st", "").strip()
        )

        # Auto-detect side from address number (SF convention: even=West, odd=East for N-S streets)
        auto_side = None
        if address_number and not request.side:
            # Even addresses on West side, odd on East side for N-S streets
            if address_number % 2 == 0:
                auto_side = "W"
            else:
                auto_side = "E"

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

        # Filter to ONLY the street the address is on (not nearby streets) - DO THIS FIRST
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

        # Use only matching street if found
        if matching_street:
            all_sweeps = matching_street

        # Filter by side AFTER corridor filter - only if explicitly requested
        # Don't auto-filter by detected side - show all options so user can choose
        if request.side:
            side_to_use = request.side.upper()
            all_sweeps = [
                s
                for s in all_sweeps
                if s.get("blockside", "").upper().startswith(side_to_use)
            ]

        # Sort by distance
        all_sweeps.sort(key=lambda x: x.get("distance_meters", float("inf")))

        # If side was explicitly specified, return only the closest match
        # Otherwise return all segments for this street so user can choose side
        if request.side and all_sweeps:
            all_sweeps = all_sweeps[:1]
        elif not request.side:
            # Show all sides for this street (no limit)
            # But group by blockside and take closest for each
            seen_sides = {}
            for s in all_sweeps:
                side = s.get("blockside", "")
                if side not in seen_sides:
                    seen_sides[side] = s
            all_sweeps = list(seen_sides.values())

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


class CalendarEventRequest(BaseModel):
    """Request to generate a calendar event for street sweeping."""

    address: str
    corridor: str
    blockside: str
    limits: str
    weekday: str
    fullname: str
    fromhour: int
    tohour: int
    week1: bool
    week2: bool
    week3: bool
    week4: bool
    week5: bool
    reminder_hours: int = 24


class CalendarEventResponse(BaseModel):
    """Response with calendar event URL."""

    calendar_url: str
    next_sweep_dates: list[str]


@router.post("/calendar")
async def create_calendar_event(request: CalendarEventRequest):
    """Generate a Google Calendar event for street sweeping reminder."""
    try:
        # Build sweep block from request
        sweep = {
            "corridor": request.corridor,
            "blockside": request.blockside,
            "limits": request.limits,
            "weekday": request.weekday,
            "fullname": request.fullname,
            "fromhour": request.fromhour,
            "tohour": request.tohour,
            "week1": request.week1,
            "week2": request.week2,
            "week3": request.week3,
            "week4": request.week4,
            "week5": request.week5,
        }

        # Generate calendar URL
        calendar_url = generate_calendar_url(
            sweep=sweep,
            address=request.address,
            reminder_hours=request.reminder_hours,
        )

        # Get next sweep dates
        dates = get_sweep_dates(sweep, months=3)
        date_strings = [d.strftime("%Y-%m-%d %H:%M") for d in dates[:8]]

        return CalendarEventResponse(
            calendar_url=calendar_url,
            next_sweep_dates=date_strings,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
