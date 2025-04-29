from datetime import datetime, timedelta
import pymongo
from bson import ObjectId 
import os
from dotenv import load_dotenv
load_dotenv()

def get_mongo_client(mongo_uri):
  """Establish connection to the MongoDB."""
  try:
    client = pymongo.MongoClient(mongo_uri, appname="devrel.content.python")
    print("Connection to MongoDB successful")
    return client
  except pymongo.errors.ConnectionFailure as e:
    print(f"Connection failed: {e}")
    return None

mongo_uri = os.environ.get("MONGO_URI")
if not mongo_uri:
  print("MONGO_URI not set in environment variables")

mongo_client = get_mongo_client(mongo_uri)

# Ingest data into MongoDB
db = mongo_client['test']
collection = db['tasks']


def get_tasks_this_week(role: str, user_id: str) -> dict:
    today = datetime.utcnow()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)          # Sunday

    query = {
        "dueDate": {
            "$gte": start_of_week,
            "$lte": end_of_week
        }
    }

    if role == "member":
        query["assignedTo"] = {"$in": [ObjectId(user_id)]}
    elif role == "admin":
        pass  # admin được xem tất cả task
    else:
        raise ValueError("Invalid role")

    tasks = list(collection.find(query))

    task_list = [
        {
            "title": task["title"],
            "dueDate": task["dueDate"].strftime("%Y-%m-%d"),
            "status": task["status"],
            "priority": task["priority"]
        }
        for task in tasks
    ]

    print(task_list)

    return {
        "total_tasks": len(task_list),
        "tasks": task_list
    }

#================
def get_all_tasks(role: str, user_id: str) -> dict:
    query = {}
    if role == "member":
        query["assignedTo"] = {"$in": [ObjectId(user_id)]}
    elif role == "admin":
        pass  # admin được xem tất cả task
    else:
        raise ValueError("Invalid role")

    tasks = list(collection.find(query))

    task_list = [
        {
            "title": task["title"],
            "dueDate": task["dueDate"].strftime("%Y-%m-%d"),
            "status": task["status"],
            "priority": task["priority"]
        }
        for task in tasks
    ]

    print(task_list)

    return {
        "total_tasks": len(task_list),
        "tasks": task_list
    }

def get_user_id_by_name(name: str) -> dict:
    user = db["users"].find_one({"name": name})
    if not user:
        raise ValueError("User not found")
    return {"user_id": str(user["_id"]), "name": name}
