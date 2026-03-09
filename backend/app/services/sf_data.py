"""
SF Street Sweeping Data Service.

Fetches and caches street sweeping schedule data from SF Open Data.
Provides spatial queries to find sweeping schedules near a given location.
"""

import logging
from typing import Optional, List, Tuple, Any
import json
import httpx

from shapely.geometry import LineString, Point
from shapely.ops import nearest_points
from shapely.strtree import STRtree

logger = logging.getLogger(__name__)

# SF Open Data API endpoint for street sweeping schedule
SF_DATA_URL = "https://data.sfgov.org/resource/yhqp-riqs.json"

# Maximum distance in meters to consider a street segment as "near"
MAX_SEARCH_RADIUS_METERS = 50


class SweepDataCache:
    """
    Cache for street sweeping data.

    Fetches data from SF Open Data API and maintains a spatial index
    for fast proximity lookups.
    """

    def __init__(self):
        self.data: List[dict] = []
        self.spatial_index: Optional[STRtree] = None
        self.geometries: List[Any] = []
        self.last_updated: Optional[str] = None

    async def load_data(self, force_refresh: bool = False):
        """
        Load sweeping data from SF Open Data API.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data.
        """
        if self.data and not force_refresh:
            logger.info("Using cached sweeping data")
            return

        logger.info(f"Fetching sweeping data from {SF_DATA_URL}")

        async with httpx.AsyncClient() as client:
            response = await client.get(SF_DATA_URL, timeout=30.0)
            response.raise_for_status()
            self.data = response.json()

        logger.info(f"Loaded {len(self.data)} street segments")
        self._build_spatial_index()

    def _build_spatial_index(self):
        """
        Build a spatial index for fast proximity queries.

        Uses Shapely's STRtree for spatial indexing.
        """
        self.geometries = []

        for record in self.data:
            if record.get("line"):
                coords = record["line"]["coordinates"]
                line = LineString(coords)
                self.geometries.append(line)
            else:
                self.geometries.append(None)

        # Create STRtree from non-None geometries
        valid_geometries = [g for g in self.geometries if g is not None]
        self.spatial_index = STRtree(valid_geometries)

        logger.info(f"Built spatial index with {len(valid_geometries)} entries")

    async def find_nearest(
        self,
        latitude: float,
        longitude: float,
        max_distance: float = MAX_SEARCH_RADIUS_METERS,
    ) -> Optional[dict]:
        """
        Find the nearest street sweeping route to a given point.

        Args:
            latitude: Latitude of the search point.
            longitude: Longitude of the search point.
            max_distance: Maximum search radius in meters.

        Returns:
            The nearest street segment record, or None if nothing nearby.
        """
        if not self.data:
            await self.load_data()

        # Create point from coordinates
        point = Point(longitude, latitude)

        # Simple approach: iterate through all geometries and find nearest
        # This is O(n) but fast enough for 1000 records
        nearest = None
        min_dist = float("inf")

        for orig_idx, geom in enumerate(self.geometries):
            if geom is None:
                continue

            # Calculate distance
            dist = point.distance(geom)

            if dist < min_dist:
                min_dist = dist
                nearest = self.data[orig_idx].copy()
                nearest["_distance_degrees"] = dist

        if nearest is None:
            logger.warning(f"No sweeping routes found near ({latitude}, {longitude})")
            return None

        # Check if within max distance (convert degrees to approximate meters)
        meters_per_degree = 111000 * (1 - 0.5 * abs(latitude) / 90)
        distance_meters = min_dist * meters_per_degree

        if distance_meters > max_distance:
            logger.warning(
                f"No sweeping routes within {max_distance}m of ({latitude}, {longitude})"
            )
            return None

        # Convert degrees to approximate meters
        nearest["_distance_meters"] = min_dist * meters_per_degree

        return nearest

    async def find_all_nearby(
        self,
        latitude: float,
        longitude: float,
        max_distance: float = MAX_SEARCH_RADIUS_METERS * 3,
    ) -> List[dict]:
        """
        Find all street sweeping routes near a given point.
        Returns multiple options to handle different sides of the street.

        Args:
            latitude: Latitude of the search point.
            longitude: Longitude of the search point.
            max_distance: Maximum search radius in meters.

        Returns:
            List of nearby street segment records.
        """
        if not self.data:
            await self.load_data()

        # Create point from coordinates
        point = Point(longitude, latitude)

        # Get corridor (street name) from nearest segment
        nearest = await self.find_nearest(
            latitude, longitude, max_distance=max_distance
        )
        if not nearest:
            return []

        target_corridor = nearest.get("corridor", "")
        logger.info(f"Looking for all segments on {target_corridor}")

        # Find all segments on same street within distance
        results = []

        for orig_idx, geom in enumerate(self.geometries):
            if geom is None:
                continue

            record = self.data[orig_idx]

            # Only include segments on the same corridor
            if record.get("corridor") != target_corridor:
                continue

            # Calculate distance
            dist = point.distance(geom)

            # Convert to meters
            meters_per_degree = 111000 * (1 - 0.5 * abs(latitude) / 90)
            dist_meters = dist * meters_per_degree

            if dist_meters <= max_distance:
                result = record.copy()
                result["_distance_meters"] = dist_meters
                results.append(result)

        # Sort by distance
        results.sort(key=lambda x: x.get("_distance_meters", float("inf")))

        logger.info(f"Found {len(results)} segments on {target_corridor}")

        return results

        if nearest is None:
            logger.warning(f"No sweeping routes found near ({latitude}, {longitude})")
            return None

        # Check if within max distance (convert degrees to approximate meters)
        meters_per_degree = 111000 * (1 - 0.5 * abs(latitude) / 90)
        distance_meters = min_dist * meters_per_degree

        if distance_meters > max_distance:
            logger.warning(
                f"No sweeping routes within {max_distance}m of ({latitude}, {longitude})"
            )
            return None

        # Convert degrees to approximate meters
        # (rough approximation - 1 degree ≈ 111km at equator)
        if nearest:
            meters_per_degree = 111000 * (1 - 0.5 * abs(latitude) / 90)
            nearest["_distance_meters"] = min_dist * meters_per_degree

        return nearest


class SFSweepingService:
    """
    Service for accessing SF street sweeping data.

    Provides methods to fetch schedules and find nearest routes.
    """

    def __init__(self):
        self.cache = SweepDataCache()

    async def find_nearest_sweep(
        self,
        latitude: float,
        longitude: float,
        max_distance: float = MAX_SEARCH_RADIUS_METERS,
    ) -> Optional[dict]:
        """
        Find the sweeping schedule nearest to a given location.

        Args:
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            max_distance: Maximum distance in meters to search.

        Returns:
            Dictionary with sweep schedule information.
        """
        # Ensure data is loaded
        await self.cache.load_data()

        # Find nearest
        nearest = await self.cache.find_nearest(latitude, longitude, max_distance)

        if not nearest:
            return None

        # Parse schedule from the record
        schedule = {
            "corridor": nearest.get("corridor"),
            "limits": nearest.get("limits"),
            "blockside": nearest.get("blockside"),
            "weekday": nearest.get("weekday"),
            "fullname": nearest.get("fullname"),
            "fromhour": int(nearest.get("fromhour", 0)),
            "tohour": int(nearest.get("tohour", 0)),
            "week1": nearest.get("week1") == "1",
            "week2": nearest.get("week2") == "1",
            "week3": nearest.get("week3") == "1",
            "week4": nearest.get("week4") == "1",
            "week5": nearest.get("week5") == "1",
            "distance_meters": nearest.get("_distance_meters"),
        }

        return schedule

    async def find_all_sweeps(
        self,
        latitude: float,
        longitude: float,
        max_distance: float = MAX_SEARCH_RADIUS_METERS * 3,
    ) -> List[dict]:
        """
        Find all sweeping schedules near a location.
        Returns multiple options to handle different sides of the street.

        Args:
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            max_distance: Maximum distance in meters to search.

        Returns:
            List of dictionaries with sweep schedule information.
        """
        # Ensure data is loaded
        await self.cache.load_data()

        # Find all nearby
        all_nearby = await self.cache.find_all_nearby(latitude, longitude, max_distance)

        if not all_nearby:
            return []

        # Parse schedules from the records
        schedules = []
        for record in all_nearby:
            schedule = {
                "corridor": record.get("corridor"),
                "limits": record.get("limits"),
                "blockside": record.get("blockside"),
                "weekday": record.get("weekday"),
                "fullname": record.get("fullname"),
                "fromhour": int(record.get("fromhour", 0)),
                "tohour": int(record.get("tohour", 0)),
                "week1": record.get("week1") == "1",
                "week2": record.get("week2") == "1",
                "week3": record.get("week3") == "1",
                "week4": record.get("week4") == "1",
                "week5": record.get("week5") == "1",
                "distance_meters": record.get("_distance_meters"),
            }
            schedules.append(schedule)

        return schedules


# Import Any for type hint
from typing import Any
