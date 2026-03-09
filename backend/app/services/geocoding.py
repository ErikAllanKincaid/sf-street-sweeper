"""
Geocoding Service.

Converts street addresses to latitude/longitude coordinates.
Uses Nominatim (OpenStreetMap) for geocoding - free and no API key required.
"""

import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# Nominatim API - free geocoding from OpenStreetMap
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"

# SF bounding box to restrict results to San Francisco
SF_BOUNDING_BOX = {
    "min_lat": 37.70,
    "max_lat": 37.82,
    "min_lon": -122.52,
    "max_lon": -122.35,
}


class GeocodingService:
    """
    Service for geocoding addresses to coordinates.

    Uses Nominatim (OpenStreetMap) for free geocoding.
    In production, could swap to Google Maps API for better accuracy.
    """

    def __init__(self):
        self._cache: dict = {}

    async def geocode(self, address: str) -> dict:
        """
        Geocode a street address to latitude/longitude.

        Args:
            address: Street address to geocode (e.g., "123 Market St, San Francisco")

        Returns:
            Dictionary with address, latitude, and longitude.

        Raises:
            ValueError: If address cannot be geocoded.
        """
        # Check cache first
        if address in self._cache:
            logger.info(f"Using cached geocode for: {address}")
            return self._cache[address]

        # Add "San Francisco" if not present
        if "san francisco" not in address.lower():
            address = f"{address}, San Francisco, CA"

        logger.info(f"Geocoding address: {address}")

        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }

        headers = {
            "User-Agent": "SF-Street-Sweeper/0.1.0",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                NOMINATIM_BASE_URL + "/search",
                params=params,
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            results = response.json()

        if not results:
            raise ValueError(f"Could not geocode address: {address}")

        result = results[0]

        lat = float(result["lat"])
        lon = float(result["lon"])

        # Check if result is within SF bounding box
        # If not, warn but still return (user might be in Daly City, etc.)
        if not self._is_in_sf_bounds(lat, lon):
            logger.warning(
                f"Geocoded address ({lat}, {lon}) is outside SF bounds. "
                f"Results may be inaccurate."
            )

        geocoded = {
            "address": result.get("display_name", address),
            "latitude": lat,
            "longitude": lon,
        }

        # Cache the result
        self._cache[address] = geocoded

        return geocoded

    def _is_in_sf_bounds(self, lat: float, lon: float) -> bool:
        """Check if coordinates are within SF bounding box."""
        return (
            SF_BOUNDING_BOX["min_lat"] <= lat <= SF_BOUNDING_BOX["max_lat"]
            and SF_BOUNDING_BOX["min_lon"] <= lon <= SF_BOUNDING_BOX["max_lon"]
        )

    async def reverse_geocode(self, latitude: float, longitude: float) -> str:
        """
        Reverse geocode - get address from coordinates.

        Args:
            latitude: Latitude coordinate.
            longitude: Longitude coordinate.

        Returns:
            Display name of the address.
        """
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "json",
        }

        headers = {
            "User-Agent": "SF-Street-Sweeper/0.1.0",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                NOMINATIM_BASE_URL + "/reverse",
                params=params,
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            result = response.json()

        return result.get("display_name", f"{latitude}, {longitude}")
