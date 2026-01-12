from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# --- User Schemas ---
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserInDB(UserCreate):
    hashed_password: str

class UserResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str = "user"

# --- Token Schema ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- Place Schema (Simplified for demo) ---
class PlaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    google_maps_url: Optional[str] = None