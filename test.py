from datetime import datetime, timedelta
import pymongo
from google.genai import types
from google import genai
from fastapi import FastAPI
from pydantic import BaseModel
from bson import ObjectId 

def get_mongo_client(mongo_uri):
  """Establish connection to the MongoDB."""
  try:
    client = pymongo.MongoClient(mongo_uri, appname="devrel.content.python")
    print("Connection to MongoDB successful")
    return client
  except pymongo.errors.ConnectionFailure as e:
    print(f"Connection failed: {e}")
    return None

mongo_uri = "mongodb+srv://duchost121:28052004@cluster0.apnnabi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
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

get_tasks_this_week_declaration = {
    "name": "get_tasks_this_week",
    "description": "Get number of tasks and their details for this week depending on user role.",
    "parameters": {
        "type": "object",
        "properties": {
            "role": {
                "type": "string",
                "description": "Role of the user, either 'admin' or 'member'.",
                "enum": ["admin", "member"],
            },
            "user_id": {
                "type": "string",
                "description": "The user's ObjectId as a string.",
            },
        },
        "required": ["role", "user_id"],
    },
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

get_all_tasks_declaration = {
    "name": "get_all_tasks",
    "description": "Get number of all tasks and their details depending on user role.",
    "parameters": {
        "type": "object",
        "properties": {
            "role": {
                "type": "string",
                "description": "Role of the user, either 'admin' or 'member'.",
                "enum": ["admin", "member"],
            },
            "user_id": {
                "type": "string",
                "description": "The user's ObjectId as a string.",
            },
        },
        "required": ["role", "user_id"],
    },
}



# Setup client
client = genai.Client(api_key="AIzaSyAP-G46fYOTSz-kNiWKmqb2QZ-Lsqfkirw")
tools = types.Tool(function_declarations=[get_tasks_this_week_declaration, get_all_tasks_declaration])
config = types.GenerateContentConfig(tools=[tools])

# Receive prompt, role, user_id from frontend
def chatbot_api(prompt: str, role: str, user_id: str):
    prompt = prompt + " here is my information\n  role: " + role + "\n user_id: " + user_id
    contents = [
        types.Content(role="user", parts=[types.Part(text=prompt)])
    ]

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=contents,
        config=config,
    )

    first_part = response.candidates[0].content.parts[0]

    if first_part.function_call:
        function_call = first_part.function_call
        args = function_call.args

        if function_call.name == "get_tasks_this_week":
            result = get_tasks_this_week(role=args["role"], user_id=args["user_id"])
        elif function_call.name == "get_all_tasks":
            result = get_all_tasks(role=args["role"], user_id=args["user_id"])
        else:
            raise ValueError(f"Unknown function call: {function_call.name}")

        # Gửi kết quả cho model để trả lời tiếp
        function_response_part = types.Part.from_function_response(
            name=function_call.name,
            response={"result": result},
        )

        contents.append(types.Content(role="model", parts=[types.Part(function_call=function_call)]))
        contents.append(types.Content(role="user", parts=[function_response_part]))

        final_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=config,
        )
        return final_response.text
    else:
        return response.text
    
app = FastAPI()

class ChatbotRequest(BaseModel):
    prompt: str
    role: str
    user_id: str

@app.post("/chatbot")
def chatbot_endpoint(request: ChatbotRequest):
    return {"response": chatbot_api(request.prompt, request.role, request.user_id)}
