from google.genai import types
from google import genai
from mongo_utils import get_tasks_this_week, get_all_tasks, get_user_id_by_name, create_task, list_all_members
import os
from dotenv import load_dotenv
from collections import defaultdict

conversation_histories = defaultdict(list)

load_dotenv()
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

get_user_id_by_name_declaration = {
    "name": "get_user_id_by_name",
    "description": "Find the user ID by their name.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The full name of the user."
            }
        },
        "required": ["name"]
    }
}

create_task_declaration = {
    "name": "create_task",
    "description": "Create a new task and assign it to a user.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Title of the task."},
            "description": {"type": "string", "description": "Detailed description of the task."},
            "priority": {"type": "string", "description": "Priority level: low, medium, high.", "enum": ["Low", "Medium", "High"]},
            "dueDate": {"type": "string", "description": "Due date in format YYYY-MM-DD."},
            "assignedTo": {"type": "string", "description": "ObjectId string of the user to assign the task to."},
            "createdBy": {"type": "string", "description": "ObjectId string of the user who created the task."},
            "todoChecklist": {
                "type": "array",
                "description": "List of checklist items for the task.",
                "items": {
                    "type": "object",
                    "properties": {
                        "_id": {"type": "string", "description": "ObjectId of the checklist item."},
                        "text": {"type": "string", "description": "Text description of the checklist item."},
                        "completed": {"type": "boolean", "description": "Indicates if the checklist item is completed."}
                    },
                    "required": ["_id", "text", "completed"]
                }
            }
        },
        "required": ["title", "description", "priority", "dueDate", "assignedTo", "createdBy", "todoChecklist"]
    }
}


list_all_members_declaration = {
    "name": "list_all_members",
    "description": "Return list of all member users.",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}

# Setup client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
tools = types.Tool(function_declarations=[
    get_tasks_this_week_declaration,
    get_all_tasks_declaration,
    get_user_id_by_name_declaration,
    create_task_declaration,
    list_all_members_declaration
])
config = types.GenerateContentConfig(tools=[tools])

# Receive prompt, role, user_id from frontend
def chatbot_api(prompt: str, role: str, user_id: str, session_id: str = None):
    if session_id is None:
        session_id = user_id  # fallback nếu frontend không gửi session_id

    # Truy xuất hoặc khởi tạo history
    contents = conversation_histories[session_id]

    # Nếu lần đầu, thêm system message
    if not contents:
        contents.append(types.Content(
            role="model",
            parts=[types.Part(text=f"You are a task-bot. Current user is {role} with id {user_id}.")]
        ))

    # Thêm user message mới
    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    ))

    # 2) Loop cho đến khi model trả text cuối cùng (không còn function_call)
    while True:
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=config,
        )
        part = resp.candidates[0].content.parts[0]

        # Nếu không có function_call => model trả lời trực tiếp
        if not part.function_call:
            contents.append(resp.candidates[0].content)  # lưu model's response
            return part.text

        # Ngược lại, xử lý function call
        fn = part.function_call
        args = fn.args

        if fn.name == "get_user_id_by_name":
            result = get_user_id_by_name(name=args["name"])
        elif fn.name == "get_tasks_this_week":
            print("get task this week =======", args)
            result = get_tasks_this_week(role=args["role"], user_id=args["user_id"])
        elif fn.name == "get_all_tasks":
            result = get_all_tasks(role=args["role"], user_id=args["user_id"])
        elif fn.name == "create_task":
            result = create_task(
                title=args["title"],
                description=args["description"],
                assigned_to_id=args["assignedTo"],
                due_date_str=args["dueDate"],
                created_by_id=user_id, 
                priority=args["priority"],
                todo_checklist=args["todoChecklist"]
            )
        elif fn.name == "list_all_members":
            result = list_all_members()
        else:
            raise ValueError(f"Unknown function: {fn.name}")

        print(result)

        # 3) Append function_call + kết quả vào history
        contents.append(types.Content(
            role="model",
            parts=[types.Part(function_call=fn)]
        ))
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_function_response(name=fn.name, response={"result": result})]
        ))
