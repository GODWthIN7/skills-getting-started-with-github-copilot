"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pymongo import MongoClient
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    # Try to connect to verify the server is available
    client.server_info()
except Exception as e:
    print(f"Warning: Could not connect to MongoDB at {MONGO_URI}. Using mongomock for development.")
    from mongomock import MongoClient
    client = MongoClient()

db = client["mergington_high_school"]
activities_collection = db["activities"]

# Initialize database with seed data if empty
def init_db():
    if activities_collection.count_documents({}) == 0:
        seed_data = [
            {
                "_id": "Chess Club",
                "description": "Learn strategies and compete in chess tournaments",
                "schedule": "Fridays, 3:30 PM - 5:00 PM",
                "max_participants": 12,
                "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
            },
            {
                "_id": "Programming Class",
                "description": "Learn programming fundamentals and build software projects",
                "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
                "max_participants": 20,
                "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
            },
            {
                "_id": "Gym Class",
                "description": "Physical education and sports activities",
                "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
                "max_participants": 30,
                "participants": ["john@mergington.edu", "olivia@mergington.edu"]
            }
        ]
        activities_collection.insert_many(seed_data)

# Initialize DB on startup
init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    activities = {}
    for doc in activities_collection.find():
        activity_name = doc["_id"]
        activities[activity_name] = {
            "description": doc["description"],
            "schedule": doc["schedule"],
            "max_participants": doc["max_participants"],
            "participants": doc["participants"]
        }
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    activity = activities_collection.find_one({"_id": activity_name})
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Add student to participants list
    activities_collection.update_one(
        {"_id": activity_name},
        {"$push": {"participants": email}}
    )
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/signup")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    activity = activities_collection.find_one({"_id": activity_name})
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Remove student from participants list
    activities_collection.update_one(
        {"_id": activity_name},
        {"$pull": {"participants": email}}
    )
    return {"message": f"Unregistered {email} from {activity_name}"}
