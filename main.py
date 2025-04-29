
from fastapi import FastAPI
from pydantic import BaseModel
from chatbot import chatbot_api

app = FastAPI()

class ChatbotRequest(BaseModel):
    prompt: str
    role: str
    user_id: str

@app.post("/chatbot")
def chatbot_endpoint(request: ChatbotRequest):
    return {"response": chatbot_api(request.prompt, request.role, request.user_id)}
