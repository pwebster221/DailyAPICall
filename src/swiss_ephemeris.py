"""Swiss Ephemeris API integration module"""

import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import structlog
from src.config import settings
from src.models import (
    SwissEphemerisResponse,
    PlanetaryPosition,
    Aspect,
    HouseCusp,
    Planet,
    AspectType
)

logger = structlog.get_logger(__name__)


class SwissEphemerisClient:
    """Client for interacting with Swiss Ephemeris API"""
    
    def __init__(self):
        self.base_url = settings.swiss_api_base_url
        self.api_key = settings.swiss_api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def get_daily_positions(
        self,
        date: Optional[datetime] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> SwissEphemerisResponse:
        """
        Fetch planetary positions for a specific date and location
        
        Args:
            date: Date for calculations (defaults to now)
            latitude: Location latitude (defaults to config)
            longitude: Location longitude (defaults to config)
        
        Returns:
            SwissEphemerisResponse with all astronomical data
        """
        if date is None:
            date = datetime.now(timezone.utc)
        
        if latitude is None:
            latitude = settings.latitude
        
        if longitude is None:
            longitude = settings.longitude
        
        logger.info(
            "Fetching ephemeris data",
            date=date.isoformat(),
            latitude=latitude,
            longitude=longitude
        )
        
        try:
            # Prepare API request
            request_data = {
                "date": date.isoformat(),
                "latitude": latitude,
                "longitude": longitude,
                "house_system": "Placidus",  # You can make this configurable
                "planets": [p.value for p in Planet],
                "aspects": {
                    "enabled": True,
                    "types": [a.value for a in AspectType],
                    "orb_factors": {
                        "Sun": 1.0,
                        "Moon": 1.0,
                        "default": 0.8
                    }
                },
                "houses": True,
                "moon_phase": True,
                "void_of_course": True
            }
            
            # Make API call
            response = await self.client.post(
                f"{self.base_url}/ephemeris",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response into models
            ephemeris_response = self._parse_response(data, date, latitude, longitude)
            
            logger.info(
                "Successfully fetched ephemeris data",
                planets_count=len(ephemeris_response.planetary_positions),
                aspects_count=len(ephemeris_response.aspects)
            )
            
            return ephemeris_response
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching ephemeris",
                status_code=e.response.status_code,
                detail=e.response.text
            )
            raise
        except Exception as e:
            logger.error("Error fetching ephemeris", error=str(e))
            raise
    
    def _parse_response(
        self,
        data: Dict[str, Any],
        date: datetime,
        latitude: float,
        longitude: float
    ) -> SwissEphemerisResponse:
        """Parse API response into structured models"""
        
        # Parse planetary positions
        positions = []
        for planet_data in data.get("planets", []):
            position = PlanetaryPosition(
                planet=planet_data["name"],
                longitude=planet_data["longitude"],
                latitude=planet_data["latitude"],
                distance=planet_data["distance"],
                speed=planet_data["speed"],
                sign=planet_data["sign"],
                degree_in_sign=planet_data["degree_in_sign"],
                house=planet_data.get("house"),
                retrograde=planet_data.get("retrograde", False)
            )
            positions.append(position)
        
        # Parse aspects
        aspects = []
        for aspect_data in data.get("aspects", []):
            aspect = Aspect(
                planet1=aspect_data["planet1"],
                planet2=aspect_data["planet2"],
                aspect_type=aspect_data["type"],
                angle=aspect_data["angle"],
                orb=aspect_data["orb"],
                applying=aspect_data.get("applying", True),
                exact_time=datetime.fromisoformat(aspect_data["exact_time"])
                if aspect_data.get("exact_time") else None
            )
            aspects.append(aspect)
        
        # Parse house cusps
        house_cusps = []
        for house_data in data.get("houses", []):
            cusp = HouseCusp(
                house=house_data["number"],
                sign=house_data["sign"],
                degree=house_data["degree"]
            )
            house_cusps.append(cusp)
        
        return SwissEphemerisResponse(
            timestamp=date,
            julian_day=data.get("julian_day", 0),
            latitude=latitude,
            longitude=longitude,
            planetary_positions=positions,
            house_cusps=house_cusps,
            aspects=aspects,
            moon_phase=data.get("moon_phase"),
            void_of_course=data.get("void_of_course")
        )
    
    async def get_planetary_hours(
        self,
        date: Optional[datetime] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate planetary hours for scheduling
        
        Returns:
            Dictionary with planetary hour information
        """
        if date is None:
            date = datetime.now(timezone.utc)
        
        if latitude is None:
            latitude = settings.latitude
        
        if longitude is None:
            longitude = settings.longitude
        
        try:
            response = await self.client.post(
                f"{self.base_url}/planetary_hours",
                json={
                    "date": date.isoformat(),
                    "latitude": latitude,
                    "longitude": longitude
                }
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error("Error fetching planetary hours", error=str(e))
            raise
    
    async def get_mercury_hour(
        self,
        date: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        Find the next Mercury hour for optimal communication timing
        
        Returns:
            Datetime of next Mercury hour
        """
        try:
            hours = await self.get_planetary_hours(date)
            
            # Find Mercury hours
            for hour in hours.get("hours", []):
                if hour["ruler"] == "Mercury":
                    hour_start = datetime.fromisoformat(hour["start_time"])
                    if hour_start > datetime.now(timezone.utc):
                        return hour_start
            
            return None
            
        except Exception as e:
            logger.error("Error finding Mercury hour", error=str(e))
            return None


# Fallback mock data for development/testing
def get_mock_ephemeris_data() -> SwissEphemerisResponse:
    """Generate mock ephemeris data for testing"""
    now = datetime.now(timezone.utc)
    
    positions = [
        PlanetaryPosition(
            planet="Sun",
            longitude=150.5,
            latitude=0.0,
            distance=1.0,
            speed=0.98,
            sign="Virgo",
            degree_in_sign=0.5,
            house=10,
            retrograde=False
        ),
        PlanetaryPosition(
            planet="Moon",
            longitude=45.2,
            latitude=2.1,
            distance=0.0026,
            speed=13.2,
            sign="Taurus",
            degree_in_sign=15.2,
            house=6,
            retrograde=False
        ),
        PlanetaryPosition(
            planet="Mercury",
            longitude=142.8,
            latitude=-1.5,
            distance=1.2,
            speed=1.5,
            sign="Virgo",
            degree_in_sign=22.8,
            house=9,
            retrograde=False
        )
    ]
    
    aspects = [
        Aspect(
            planet1="Sun",
            planet2="Moon",
            aspect_type="Trine",
            angle=120.0,
            orb=2.3,
            applying=True,
            exact_time=None
        )
    ]
    
    house_cusps = [
        HouseCusp(house=i, sign="Aries", degree=i * 30.0)
        for i in range(1, 13)
    ]
    
    return SwissEphemerisResponse(
        timestamp=now,
        julian_day=2460000.5,
        latitude=settings.latitude,
        longitude=settings.longitude,
        planetary_positions=positions,
        house_cusps=house_cusps,
        aspects=aspects,
        moon_phase=0.25,
        void_of_course=False
    )