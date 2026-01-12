from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Import our modules
from database import db, fix_id, client
from models import PlaceCreate
from auth import auth_router, get_password_hash, get_current_user
from wishlist import wishlist_router

app = FastAPI()

# Include routers
app.include_router(auth_router)
app.include_router(wishlist_router)

# --- STARTUP EVENT ---
@app.on_event("startup")
async def startup_db_client():
    try:
        await client.admin.command('ping')
        print("\n✅ Successfully connected to MongoDB!")
        print(f"📦 Database: {db.name}")
        
        # Check and initialize users collection
        user_count = await db.users.count_documents({})
        if user_count == 0:
            print("📋 No users found. Creating default admin user...")
            default_user = {
                "full_name": os.getenv("DEFAULT_USER_NAME"),
                "email": os.getenv("DEFAULT_USER_EMAIL"),
                "role": os.getenv("DEFAULT_USER_ROLE", "admin"),
                "hashed_password": get_password_hash(os.getenv("DEFAULT_USER_PASSWORD")),
                "created_at": datetime.utcnow()
            }
            await db.users.insert_one(default_user)
            print("👤 Default admin user created successfully!")
        else:
            print(f"👥 Users collection exists with {user_count} user(s)")
        
        # Check and initialize wishlists collection
        collections = await db.list_collection_names()
        if "wishlists" not in collections:
            await db.create_collection("wishlists")
            print("📍 Wishlists collection created!")
        else:
            wishlist_count = await db.wishlists.count_documents({})
            print(f"📍 Wishlists collection exists with {wishlist_count} item(s)")
            
    except Exception as e:
        print(f"\n❌ Failed to connect to MongoDB: {e}")

# --- CORS SETUP ---
# This allows your Nuxt frontend to talk to this backend
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTES ---

@app.post("/places/")
async def create_place(place: PlaceCreate, current_user: dict = Depends(get_current_user)):
    # This route is PROTECTED. Only logged in users can reach here.
    place_dict = place.dict()
    place_dict["user_id"] = current_user["id"] # Link place to the logged-in user
    
    new_place = await db.places.insert_one(place_dict)
    return {"message": "Place added", "id": str(new_place.inserted_id)}