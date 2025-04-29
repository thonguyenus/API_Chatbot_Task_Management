from google.genai import types
from google import genai
from mongo_utils import get_tasks_this_week, get_all_tasks, get_user_id_by_name
import os
from dotenv import load_dotenv

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


# Setup client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
tools = types.Tool(function_declarations=[get_tasks_this_week_declaration, get_all_tasks_declaration, get_user_id_by_name_declaration])
config = types.GenerateContentConfig(tools=[tools])

# Receive prompt, role, user_id from frontend
def chatbot_api(prompt: str, role: str, user_id: str):
    # 1) Khởi tạo contents như trên
    contents = [
        types.Content(
            role="model",
            parts=[types.Part(text=f"You are a task-bot. Current user is {role} with id {user_id}.")]
        ),
        types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
    ]

    # 2) Loop cho đến khi model trả text cuối cùng (không có function_call)
    while True:
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=config,
        )
        part = resp.candidates[0].content.parts[0]

        # Nếu không có function_call thì đây là kết quả cuối
        if not part.function_call:
            return part.text

        # Ngược lại, lấy function_call và chạy hàm tương ứng
        fn = part.function_call
        args = fn.args
        if fn.name == "get_user_id_by_name":
            result = get_user_id_by_name(name=args["name"])
        elif fn.name == "get_tasks_this_week":
            result = get_tasks_this_week(role=args["role"], user_id=args["user_id"])
        elif fn.name == "get_all_tasks":
            result = get_all_tasks(role=args["role"], user_id=args["user_id"])
        else:
            raise ValueError(f"Unknown function: {fn.name}")

        print(result)
        # 3) Append cả function_call lẫn kết quả hàm vào contents
        contents.append(types.Content(
            role="model",
            parts=[types.Part(function_call=fn)]
        ))
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_function_response(name=fn.name, response={"result": result})]
        ))
