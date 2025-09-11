"""Data models for the astrological pipeline"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class Planet(str, Enum):
    """Enumeration of celestial bodies"""
    SUN = "Sun"
    MOON = "Moon"
    MERCURY = "Mercury"
    VENUS = "Venus"
    MARS = "Mars"
    JUPITER = "Jupiter"
    SATURN = "Saturn"
    URANUS = "Uranus"
    NEPTUNE = "Neptune"
    PLUTO = "Pluto"
    NORTH_NODE = "North Node"
    SOUTH_NODE = "South Node"
    CHIRON = "Chiron"
    LILITH = "Lilith"


class ZodiacSign(str, Enum):
    """Enumeration of zodiac signs"""
    ARIES = "Aries"
    TAURUS = "Taurus"
    GEMINI = "Gemini"
    CANCER = "Cancer"
    LEO = "Leo"
    VIRGO = "Virgo"
    LIBRA = "Libra"
    SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN = "Capricorn"
    AQUARIUS = "Aquarius"
    PISCES = "Pisces"


class AspectType(str, Enum):
    """Types of planetary aspects"""
    CONJUNCTION = "Conjunction"
    OPPOSITION = "Opposition"
    TRINE = "Trine"
    SQUARE = "Square"
    SEXTILE = "Sextile"
    QUINCUNX = "Quincunx"
    SEMISEXTILE = "Semi-sextile"
    SEMISQUARE = "Semi-square"
    SESQUIQUADRATE = "Sesquiquadrate"


class HermeticPrinciple(str, Enum):
    """The Seven Hermetic Principles"""
    MENTALISM = "Mentalism"
    CORRESPONDENCE = "Correspondence"
    VIBRATION = "Vibration"
    POLARITY = "Polarity"
    RHYTHM = "Rhythm"
    CAUSE_AND_EFFECT = "Cause and Effect"
    GENDER = "Gender"


# Swiss Ephemeris API Models
class PlanetaryPosition(BaseModel):
    """Position of a celestial body"""
    planet: str
    longitude: float = Field(..., description="Ecliptic longitude in degrees")
    latitude: float = Field(..., description="Ecliptic latitude in degrees")
    distance: float = Field(..., description="Distance from Earth in AU")
    speed: float = Field(..., description="Daily motion in degrees")
    sign: str = Field(..., description="Zodiac sign")
    degree_in_sign: float = Field(..., description="Degree within the sign")
    house: Optional[int] = Field(None, description="House placement (1-12)")
    retrograde: bool = Field(default=False, description="Is planet retrograde")


class Aspect(BaseModel):
    """Aspect between two celestial bodies"""
    planet1: str
    planet2: str
    aspect_type: str
    angle: float = Field(..., description="Exact angle in degrees")
    orb: float = Field(..., description="Orb of influence in degrees")
    applying: bool = Field(..., description="Is aspect applying or separating")
    exact_time: Optional[datetime] = None


class HouseCusp(BaseModel):
    """House cusp position"""
    house: int = Field(..., ge=1, le=12)
    sign: str
    degree: float = Field(..., ge=0, lt=360)


class SwissEphemerisResponse(BaseModel):
    """Response from Swiss Ephemeris API"""
    timestamp: datetime
    julian_day: float
    latitude: float
    longitude: float
    planetary_positions: List[PlanetaryPosition]
    house_cusps: List[HouseCusp]
    aspects: List[Aspect]
    moon_phase: Optional[float] = None
    void_of_course: Optional[bool] = None


# Interpretation Models
class ArchetypalActivation(BaseModel):
    """Activation of an archetype from the 78"""
    archetype_id: str = Field(..., description="ID from your 78 archetypes")
    archetype_name: str
    activation_strength: float = Field(..., ge=0, le=1)
    trigger_planet: Optional[str] = None
    trigger_aspect: Optional[str] = None
    trigger_house: Optional[int] = None


class TransitInterpretation(BaseModel):
    """Interpretation of a single transit"""
    transit_id: str = Field(..., description="Unique ID for this transit")
    planet: str
    sign: str
    house: Optional[int] = None
    aspects: List[Aspect] = []
    activated_archetypes: List[ArchetypalActivation] = []
    hermetic_principles: List[str] = []
    interpretation_text: str
    significance_score: float = Field(..., ge=0, le=1)
    keywords: List[str] = []


class DailyInterpretation(BaseModel):
    """Complete daily astrological interpretation"""
    date: datetime
    location: Dict[str, float] = Field(..., description="lat, lon coordinates")
    raw_ephemeris: SwissEphemerisResponse
    transits: List[TransitInterpretation]
    primary_theme: str
    secondary_themes: List[str] = []
    activated_archetypes_summary: List[ArchetypalActivation]
    hermetic_synthesis: Dict[str, str]
    daily_guidance: str
    warnings: Optional[List[str]] = None
    opportunities: Optional[List[str]] = None
    meditation_focus: Optional[str] = None


# Email Models
class EmailContent(BaseModel):
    """Formatted email content"""
    subject: str
    greeting: str
    daily_overview: str
    transit_narratives: List[str]
    archetypal_insights: str
    practical_guidance: str
    meditation_suggestion: Optional[str] = None
    closing: str
    full_html: str
    plain_text: str


# Neo4j Models
class CypherQuery(BaseModel):
    """Cypher query for Neo4j"""
    query: str
    parameters: Dict[str, Any] = {}
    description: str
    transaction_group: Optional[str] = None


class Neo4jTransaction(BaseModel):
    """Collection of Cypher queries to run as transaction"""
    transaction_id: str
    queries: List[CypherQuery]
    rollback_queries: Optional[List[CypherQuery]] = None
    verification_query: Optional[CypherQuery] = None


class GraphUpdate(BaseModel):
    """Result of Neo4j graph update"""
    transaction_id: str
    success: bool
    nodes_created: int = 0
    relationships_created: int = 0
    properties_set: int = 0
    error_message: Optional[str] = None
    verification_result: Optional[Dict[str, Any]] = None


# Pipeline Models
class PipelineStage(str, Enum):
    """Stages of the processing pipeline"""
    FETCH_EPHEMERIS = "fetch_ephemeris"
    INTERPRET_ASTROLOGY = "interpret_astrology"
    FORMAT_EMAIL = "format_email"
    GENERATE_CYPHER = "generate_cypher"
    SEND_EMAIL = "send_email"
    UPDATE_GRAPH = "update_graph"
    VERIFY_GRAPH = "verify_graph"


class PipelineResult(BaseModel):
    """Result of complete pipeline execution"""
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool
    stages_completed: List[PipelineStage] = []
    stages_failed: List[PipelineStage] = []
    ephemeris_data: Optional[SwissEphemerisResponse] = None
    interpretation: Optional[DailyInterpretation] = None
    email_sent: bool = False
    graph_updated: bool = False
    errors: List[Dict[str, Any]] = []
    retry_count: int = 0


# Error Models
class PipelineError(BaseModel):
    """Error during pipeline execution"""
    stage: PipelineStage
    error_type: str
    error_message: str
    timestamp: datetime
    retry_attempted: bool = False
    fatal: bool = False
