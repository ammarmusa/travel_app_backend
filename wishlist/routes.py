from fastapi import APIRouter, HTTPException, Depends, status
from typing import List

from auth.controller import get_current_user
from .model import (
    WishlistCreate,
    WishlistUpdate,
    WishlistResponse,
    ActivityCreate,
    ActivityUpdate,
    ActivityResponse
)
from .controller import (
    get_user_wishlists,
    get_all_wishlists,
    get_wishlist_by_id,
    create_wishlist,
    update_wishlist,
    delete_wishlist,
    add_activity,
    update_activity,
    delete_activity
)

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


@router.post("/", response_model=WishlistResponse, status_code=status.HTTP_201_CREATED)
async def create_wishlist_place(
    wishlist: WishlistCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new wishlist place.
    
    You can either:
    - Provide latitude and longitude manually (source_type will be 'manual')
    - Provide a google_maps_url and coordinates will be extracted automatically (source_type will be 'google_map')
    """
    wishlist_data = wishlist.dict()
    
    # Validate: must have either coordinates or google_maps_url
    has_coordinates = wishlist_data.get("latitude") is not None and wishlist_data.get("longitude") is not None
    has_url = wishlist_data.get("google_maps_url") is not None
    
    if not has_coordinates and not has_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either provide latitude/longitude or google_maps_url"
        )
    
    result = await create_wishlist(wishlist_data, current_user["id"])
    return result


@router.get("/", response_model=List[WishlistResponse])
async def get_all_wishlist_places(current_user: dict = Depends(get_current_user)):
    """Get all wishlist places from all users."""
    return await get_all_wishlists()


@router.get("/{wishlist_id}", response_model=WishlistResponse)
async def get_wishlist(
    wishlist_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific wishlist place by ID."""
    wishlist = await get_wishlist_by_id(wishlist_id)
    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )
    return wishlist


@router.put("/{wishlist_id}", response_model=WishlistResponse)
async def update_wishlist_place(
    wishlist_id: str,
    wishlist: WishlistUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a wishlist place."""
    result = await update_wishlist(wishlist_id, current_user["id"], wishlist.dict())
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )
    return result


@router.delete("/{wishlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wishlist_place(
    wishlist_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a wishlist place."""
    success = await delete_wishlist(wishlist_id, current_user["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )
    return None


# --- Activity Routes ---

@router.post("/{wishlist_id}/activities", response_model=WishlistResponse)
async def create_activity(
    wishlist_id: str,
    activity: ActivityCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a new activity to a wishlist place."""
    result = await add_activity(wishlist_id, current_user["id"], activity.dict())
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )
    return result


@router.put("/{wishlist_id}/activities/{activity_id}", response_model=WishlistResponse)
async def update_wishlist_activity(
    wishlist_id: str,
    activity_id: str,
    activity: ActivityUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an activity in a wishlist place."""
    result = await update_activity(
        wishlist_id, 
        current_user["id"], 
        activity_id, 
        activity.dict()
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist or activity not found"
        )
    return result


@router.delete("/{wishlist_id}/activities/{activity_id}", response_model=WishlistResponse)
async def delete_wishlist_activity(
    wishlist_id: str,
    activity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an activity from a wishlist place."""
    result = await delete_activity(wishlist_id, current_user["id"], activity_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist or activity not found"
        )
    return result
