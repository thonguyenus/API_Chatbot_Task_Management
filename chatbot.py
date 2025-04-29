from google.genai import types
from google import genai
from mongo_utils import get_tasks_this_week, get_all_tasks


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