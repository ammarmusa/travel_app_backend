from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# --- User Schemas ---
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    full_name: str
    email: EmailStr
    hashed_password: str
    role: str = "user"
    created_at: Optional[datetime] = None


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str = "user"


# --- Token Schema ---
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
