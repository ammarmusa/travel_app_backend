import re
import uuid
import httpx
from datetime import datetime
from typing import Optional, Tuple, List
from bson import ObjectId
from fastapi import HTTPException, status

from database import db, fix_id


async def extract_coordinates_from_url(google_maps_url: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract latitude and longitude from Google Maps URL.
    Handles both short URLs (goo.gl/maps/...) and full URLs.
    """
    try:
        final_url = google_maps_url
        
        # Follow redirects for short URLs
        if "goo.gl" in google_maps_url or "maps.app.goo.gl" in google_maps_url:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(google_maps_url)
                final_url = str(response.url)
        
        # Pattern 1: @lat,lng,zoom (most common)
        pattern1 = r"@(-?\d+\.?\d*),(-?\d+\.?\d*)"
        match = re.search(pattern1, final_url)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        # Pattern 2: !3d{lat}!4d{lng}
        pattern2 = r"!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)"
        match = re.search(pattern2, final_url)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        # Pattern 3: query parameters ll=lat,lng
        pattern3 = r"ll=(-?\d+\.?\d*),(-?\d+\.?\d*)"
        match = re.search(pattern3, final_url)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        # Pattern 4: /place/lat,lng
        pattern4 = r"/place/(-?\d+\.?\d*),(-?\d+\.?\d*)"
        match = re.search(pattern4, final_url)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        return None, None
        
    except Exception as e:
        print(f"Error extracting coordinates: {e}")
        return None, None


async def get_user_wishlists(user_id: str) -> List[dict]:
    """Get all wishlists for a user."""
    cursor = db.wishlists.find({"user_id": user_id})
    wishlists = []
    async for wishlist in cursor:
        wishlists.append(fix_id(wishlist))
    return wishlists


async def get_all_wishlists() -> List[dict]:
    """Get all wishlists from all users."""
    cursor = db.wishlists.find({})
    wishlists = []
    async for wishlist in cursor:
        wishlists.append(fix_id(wishlist))
    return wishlists


async def get_wishlist_by_id(wishlist_id: str, user_id: str = None) -> Optional[dict]:
    """Get a specific wishlist by ID. If user_id is provided, ensures it belongs to the user."""
    try:
        query = {"_id": ObjectId(wishlist_id)}
        if user_id:
            query["user_id"] = user_id
        wishlist = await db.wishlists.find_one(query)
        return fix_id(wishlist) if wishlist else None
    except Exception:
        return None


async def create_wishlist(wishlist_data: dict, user_id: str) -> dict:
    """Create a new wishlist place."""
    # Determine source type and extract coordinates if needed
    if wishlist_data.get("google_maps_url"):
        lat, lng = await extract_coordinates_from_url(wishlist_data["google_maps_url"])
        wishlist_data["latitude"] = lat
        wishlist_data["longitude"] = lng
        wishlist_data["source_type"] = "google_map"
    else:
        wishlist_data["source_type"] = "manual"
    
    # Prepare document
    wishlist_data["user_id"] = user_id
    wishlist_data["activities"] = []
    wishlist_data["created_at"] = datetime.utcnow()
    
    # Insert into database
    result = await db.wishlists.insert_one(wishlist_data)
    created = await db.wishlists.find_one({"_id": result.inserted_id})
    return fix_id(created)


async def update_wishlist(wishlist_id: str, user_id: str, update_data: dict) -> Optional[dict]:
    """Update an existing wishlist."""
    # Remove None values
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    if not update_data:
        return await get_wishlist_by_id(wishlist_id, user_id)
    
    # If updating Google Maps URL, re-extract coordinates
    if "google_maps_url" in update_data and update_data["google_maps_url"]:
        lat, lng = await extract_coordinates_from_url(update_data["google_maps_url"])
        update_data["latitude"] = lat
        update_data["longitude"] = lng
        update_data["source_type"] = "google_map"
    
    try:
        result = await db.wishlists.update_one(
            {"_id": ObjectId(wishlist_id), "user_id": user_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            return None
        return await get_wishlist_by_id(wishlist_id, user_id)
    except Exception:
        return None


async def delete_wishlist(wishlist_id: str, user_id: str) -> bool:
    """Delete a wishlist."""
    try:
        result = await db.wishlists.delete_one({
            "_id": ObjectId(wishlist_id),
            "user_id": user_id
        })
        return result.deleted_count > 0
    except Exception:
        return False


async def add_activity(wishlist_id: str, user_id: str, activity_data: dict) -> Optional[dict]:
    """Add an activity to a wishlist."""
    # Generate unique ID for the activity
    activity_data["id"] = str(uuid.uuid4())
    
    try:
        result = await db.wishlists.update_one(
            {"_id": ObjectId(wishlist_id), "user_id": user_id},
            {"$push": {"activities": activity_data}}
        )
        if result.matched_count == 0:
            return None
        return await get_wishlist_by_id(wishlist_id, user_id)
    except Exception:
        return None


async def update_activity(
    wishlist_id: str, 
    user_id: str, 
    activity_id: str, 
    update_data: dict
) -> Optional[dict]:
    """Update an activity within a wishlist."""
    # Remove None values
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    if not update_data:
        return await get_wishlist_by_id(wishlist_id, user_id)
    
    # Build update query for nested array
    set_fields = {f"activities.$.{k}": v for k, v in update_data.items()}
    
    try:
        result = await db.wishlists.update_one(
            {
                "_id": ObjectId(wishlist_id),
                "user_id": user_id,
                "activities.id": activity_id
            },
            {"$set": set_fields}
        )
        if result.matched_count == 0:
            return None
        return await get_wishlist_by_id(wishlist_id, user_id)
    except Exception:
        return None


async def delete_activity(wishlist_id: str, user_id: str, activity_id: str) -> Optional[dict]:
    """Delete an activity from a wishlist."""
    try:
        result = await db.wishlists.update_one(
            {"_id": ObjectId(wishlist_id), "user_id": user_id},
            {"$pull": {"activities": {"id": activity_id}}}
        )
        if result.matched_count == 0:
            return None
        return await get_wishlist_by_id(wishlist_id, user_id)
    except Exception:
        return None
