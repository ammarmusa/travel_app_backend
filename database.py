import os
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv()

# Get DB URL from .env file
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://admin:1qaz!QAZ1qaz@travelapp.dgyto1m.mongodb.net/?appName=TravelApp") 

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.travel_app  # The DB name is 'travel_app'

# Helper to fix MongoDB _id to string for Pydantic
# Because MongoDB uses ObjectId(), but JSON needs Strings
def fix_id(doc):
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc
