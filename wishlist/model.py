from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class WishlistStatus(str, Enum):
    WISHLIST = "Wishlist"
    PLANNED = "Planned"
    VISITED = "Visited"


class SourceType(str, Enum):
    MANUAL = "manual"
    GOOGLE_MAP = "google_map"


# --- Activity Schemas ---
class ActivityBase(BaseModel):
    name: str
    cost: float = 0.00
    is_completed: bool = False


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    cost: Optional[float] = None
    is_completed: Optional[bool] = None


class ActivityResponse(ActivityBase):
    id: str


# --- Wishlist Schemas ---
class WishlistBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: WishlistStatus = WishlistStatus.WISHLIST


class WishlistCreate(WishlistBase):
    # For manual entry
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # For Google Maps import
    google_maps_url: Optional[str] = None


class WishlistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WishlistStatus] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_maps_url: Optional[str] = None


class WishlistResponse(WishlistBase):
    id: str
    user_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_maps_url: Optional[str] = None
    source_type: SourceType
    activities: List[ActivityResponse] = []
    created_at: datetime
