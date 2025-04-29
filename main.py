
from fastapi import FastAPI
from pydantic import BaseModel
from chatbot import chatbot_api
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # hoặc ["*"] cho mọi domain (không khuyến khích production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ChatbotRequest(BaseModel):
    prompt: str
    role: str
    user_id: str
    session_id: str = None

@app.post("/chatbot")
def chatbot_endpoint(request: ChatbotRequest):
    return {
        "response": chatbot_api(
            prompt=request.prompt,
            role=request.role,
            user_id=request.user_id,
            session_id=request.session_id
        )
    }
