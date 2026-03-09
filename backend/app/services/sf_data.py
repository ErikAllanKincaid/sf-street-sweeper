"""
SF Street Sweeping Data Service.

Fetches and caches street sweeping schedule data from SF Open Data.
Provides spatial queries to find sweeping schedules near a given location.
"""

import logging
from typing import Optional, List, Tuple
import json
import httpx

from shapely.geometry import LineString, Point
from shapely.ops import nearest_points

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
        self.spatial_index: Optional[Any] = None  # R-tree spatial index
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

        Uses R-tree to index all street segment geometries.
        """
        from rtree import index

        # Create spatial index
        self.spatial_index = index.Index()

        for idx, record in enumerate(self.data):
            if record.get("line"):
                coords = record["line"]["coordinates"]
                line = LineString(coords)

                # Insert into R-tree with bounding box
                minx, miny, maxx, maxy = line.bounds
                self.spatial_index.insert(idx, (minx, miny, maxx, maxy))

        logger.info(f"Built spatial index with {self.spatial_index.count()} entries")

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

        # Search in bounding box first (approximate degrees to meters)
        # 1 degree latitude ≈ 111km, 1 degree longitude varies by latitude
        lat_degree = max_distance / 111000
        lon_degree = max_distance / (111000 * abs(latitude))

        bbox = (
            longitude - lon_degree,
            latitude - lat_degree,
            longitude + lon_degree,
            latitude + lat_degree,
        )

        # Find candidates within bounding box
        candidates = list(self.spatial_index.intersection(bbox))

        if not candidates:
            logger.warning(f"No sweeping routes found near ({latitude}, {longitude})")
            return None

        # Find nearest among candidates
        nearest = None
        min_dist = float("inf")

        for idx in candidates:
            record = self.data[idx]
            if record.get("line"):
                coords = record["line"]["coordinates"]
                line = LineString(coords)

                # Calculate distance
                dist = point.distance(line)

                if dist < min_dist:
                    min_dist = dist
                    nearest = record
                    nearest["_distance_degrees"] = dist

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


# Import Any for type hint
from typing import Any
