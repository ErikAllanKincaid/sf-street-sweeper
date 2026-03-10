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

# SF Open Data API endpoint for street sweeping schedule (ARCHIVED SNAPSHOT)
# Note: xsry-uuyt is the frozen Jan 27, 2025 snapshot (37,878 rows)
# yhqp-riqs is BROKEN/UNRELIABLE (only 220 rows, under maintenance)
SF_DATA_URL = "https://data.sfgov.org/resource/xsry-uuyt.json?$limit=40000"

# Maximum distance in meters to consider a street segment as "near"
MAX_SEARCH_RADIUS_METERS = 200  # Increased for broader neighborhood search
MAX_SEARCH_RADIUS_METERS_WIDE = 1000  # Wide search to find ANY nearby street


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

        # Always return the nearest street, even beyond max_distance
        # This allows us to show available options to users
        meters_per_degree = 111000 * (1 - 0.5 * abs(latitude) / 90)
        distance_meters = min_dist * meters_per_degree

        if distance_meters > max_distance:
            logger.warning(
                f"No sweeping routes within {max_distance}m of ({latitude}, {longitude})"
            )
        # Note: We still return the record anyway so user can see options

        # Convert degrees to approximate meters
        nearest["_distance_meters"] = min_dist * meters_per_degree
        nearest["_distance_meters_warning"] = distance_meters > max_distance

        return nearest

    async def find_all_nearby(
        self,
        latitude: float,
        longitude: float,
        max_distance: float = MAX_SEARCH_RADIUS_METERS,
    ) -> List[dict]:
        """
        Find all street sweeping routes near a given point.
        Returns nearby streets even if on different corridor (to show available options).

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

        # Find the nearest ANY street (not just same corridor)
        nearest_any = await self.find_nearest(
            latitude, longitude, max_distance=max_distance
        )

        if not nearest_any:
            return []

        # Get the corridor of the nearest street
        target_corridor = nearest_any.get("corridor", "")
        logger.info(f"Nearest corridor: {target_corridor}")

        # Find ALL segments (any corridor), sorted by distance
        results = []

        for orig_idx, geom in enumerate(self.geometries):
            if geom is None:
                continue

            record = self.data[orig_idx]

            # Calculate distance
            dist = point.distance(geom)

            # Convert to meters
            meters_per_degree = 111000 * (1 - 0.5 * abs(latitude) / 90)
            dist_meters = dist * meters_per_degree

            # Always include, sorted by distance
            result = record.copy()
            result["_distance_meters"] = dist_meters
            results.append(result)

        # Sort by distance
        results.sort(key=lambda x: x.get("_distance_meters", float("inf")))

        logger.info(f"Found {len(results)} segments")
        return results

        # Dead code below, removed


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
        limit: int = 50,
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

        # Apply limit
        if limit:
            all_nearby = all_nearby[:limit]

        if not all_nearby:
            return []

        # Parse schedules from the records
        schedules = []
        for record in all_nearby:
            schedule = {
                "corridor": record.get("corridor"),
                "limits": record.get("limits"),
                "blockside": record.get("blockside", ""),
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

    async def get_available_streets(
        self,
        latitude: float,
        longitude: float,
    ):
        """
        Get all corridor names (street names) available in the dataset.
        Useful when no exact match is found for a location.

        Args:
            latitude: Latitude (used for distance calculation)
            longitude: Longitude (used for distance calculation)

        Returns:
            Sorted list of corridor names.
        """
        await self.cache.load_data()

        point = Point(longitude, latitude)
        available_corridors = []

        for orig_idx, geom in enumerate(self.cache.geometries):
            if geom is None:
                continue

            corridor = self.cache.data[orig_idx].get("corridor")
            if corridor and corridor not in available_corridors:
                available_corridors.append(corridor)

        # Calculate and display distances as a courtesy
        corridor_details = []
        for corridor in available_corridors:
            # Find this corridor's closest point
            corridor_geometries = [
                g
                for idx, g in enumerate(self.cache.geometries)
                if self.cache.data[idx].get("corridor") == corridor and g is not None
            ]
            if corridor_geometries:
                # Get closest for this corridor
                closest_geom = corridor_geometries[0]
                dist = point.distance(closest_geom)
                meters_per_degree = 111000 * (1 - 0.5 * abs(latitude) / 90)
                dist_meters = dist * meters_per_degree
                corridor_details.append(
                    {
                        "corridor": corridor,
                        "distance_meters": dist_meters,
                        "week1": self.cache.data[
                            next(
                                i
                                for i, g in enumerate(self.cache.geometries)
                                if self.cache.data[i].get("corridor") == corridor
                            )
                        ].get("week1", "N/A"),
                    }
                )

        corridor_details.sort(key=lambda x: x["distance_meters"])
        return corridor_details


# Import Any for type hint
from typing import Any
