"""Location-related data models for the Ad Management system."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class Location(BaseModel):
    """Location model for targeting."""
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State or province")
    zip_code: Optional[str] = Field(None, description="ZIP or postal code")
    country: str = Field(default="US", description="Country code")
    location_code: Optional[int] = Field(None, description="DataForSEO location code")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    radius_miles: Optional[int] = Field(None, ge=1, le=500, description="Targeting radius in miles")
    population: Optional[int] = Field(None, ge=0, description="Population count")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('zip_code')
    def validate_zip_code(cls, v):
        """Validate and clean ZIP code."""
        if v:
            # Remove any non-alphanumeric characters
            v = ''.join(c for c in v if c.isalnum() or c == '-')
            # For US ZIP codes, ensure proper format
            if len(v) == 5 and v.isdigit():
                return v
            elif len(v) == 9 and v.isdigit():
                return f"{v[:5]}-{v[5:]}"
            # Return as-is for international postal codes
            return v
        return v
    
    @field_validator('state')
    def normalize_state(cls, v):
        """Normalize state abbreviations."""
        if v and len(v) == 2:
            return v.upper()
        return v
    
    def to_search_string(self) -> str:
        """Convert location to search string format."""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.zip_code:
            parts.append(self.zip_code)
        return ", ".join(parts) if parts else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'country': self.country,
            'location_code': self.location_code,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'radius_miles': self.radius_miles,
            'population': self.population,
            'metadata': self.metadata
        }


class LocationGroup(BaseModel):
    """Group of locations for campaign targeting."""
    name: str = Field(..., description="Location group name")
    description: Optional[str] = Field(None, description="Group description")
    locations: List[Location] = Field(default_factory=list, description="List of locations in group")
    targeting_type: str = Field(default="include", pattern="^(include|exclude)$")
    priority: int = Field(default=1, ge=1, le=10, description="Priority level")
    created_at: datetime = Field(default_factory=datetime.now)
    
    def add_location(self, location: Location):
        """Add a location to the group."""
        self.locations.append(location)
    
    def remove_location(self, location: Location):
        """Remove a location from the group."""
        if location in self.locations:
            self.locations.remove(location)
    
    def get_location_codes(self) -> List[int]:
        """Get all location codes from the group."""
        return [loc.location_code for loc in self.locations if loc.location_code]
    
    def get_zip_codes(self) -> List[str]:
        """Get all ZIP codes from the group."""
        return [loc.zip_code for loc in self.locations if loc.zip_code]
    
    def get_cities(self) -> List[str]:
        """Get all cities from the group."""
        return [loc.city for loc in self.locations if loc.city]


class LocationRadius(BaseModel):
    """Location with radius for proximity targeting."""
    center_location: Location = Field(..., description="Center point location")
    radius_miles: int = Field(..., ge=1, le=500, description="Radius in miles")
    radius_km: Optional[float] = Field(None, ge=1, le=800, description="Radius in kilometers")
    include_surrounding: bool = Field(default=True, description="Include surrounding areas")
    
    @field_validator('radius_km')
    def calculate_km_from_miles(cls, v, values):
        """Calculate kilometers from miles if not provided."""
        if v is None and 'radius_miles' in values:
            return values['radius_miles'] * 1.60934
        return v
    
    def contains_location(self, location: Location) -> bool:
        """Check if a location falls within the radius."""
        # This would require actual distance calculation using coordinates
        # Simplified implementation for now
        if not (self.center_location.latitude and self.center_location.longitude and
                location.latitude and location.longitude):
            return False
        
        # Haversine formula for distance calculation would go here
        # For now, return True as placeholder
        return True


class MarketArea(BaseModel):
    """Market area definition for campaign targeting."""
    name: str = Field(..., description="Market area name")
    primary_locations: List[Location] = Field(default_factory=list, description="Primary target locations")
    secondary_locations: List[Location] = Field(default_factory=list, description="Secondary target locations")
    excluded_locations: List[Location] = Field(default_factory=list, description="Locations to exclude")
    market_type: str = Field(default="local", pattern="^(local|regional|national|international)$")
    estimated_reach: Optional[int] = Field(None, ge=0, description="Estimated population reach")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_all_locations(self) -> List[Location]:
        """Get all locations (primary and secondary)."""
        return self.primary_locations + self.secondary_locations
    
    def get_targeting_summary(self) -> Dict[str, Any]:
        """Get summary of targeting setup."""
        return {
            'name': self.name,
            'market_type': self.market_type,
            'primary_count': len(self.primary_locations),
            'secondary_count': len(self.secondary_locations),
            'excluded_count': len(self.excluded_locations),
            'estimated_reach': self.estimated_reach
        }