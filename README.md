Task Manager Chatbot API (RAG + Gemini Function Calling)

This project is a FastAPI-based backend that supports a smart task assistant chatbot, capable of understanding user queries, calling relevant functions, and performing semantic search on tasks using Google Gemini and MongoDB.

📁 Project Structure

├── main.py                    # FastAPI entrypoint for chatbot endpoint
├── chatbot.py                 # Core chatbot logic with Gemini + function calling
├── create_embed_task.py       # Script to embed task title/description into MongoDB
├── mongo_utils.py             # Helper functions for database access
├── embed_utils.py             # Gemini embedding logic
├── .env                       # Your environment variables (GEMINI_API_KEY, DB_URI, etc.)
└── requirements.txt

Setup Instructions
1. Clone & Install Dependencies
git clone https://github.com/yourusername/task-chatbot-api.git
cd task-chatbot-api
pip install -r requirements.txt
2. Setup Environment Variables
Create a .env file in the root directory:
GEMINI_API_KEY=your_google_gemini_api_key
MONGO_URI=your_mongodb_uri
3. Embed All Tasks (Initial Setup)
This step generates embeddings for all tasks and stores them in MongoDB.
python create_embed_task.py
🚀 Running the API Server
Start the FastAPI server with:
uvicorn main:app --reload --port 8000
Now the chatbot API will be available at:
http://localhost:8000/chatbot
🧠 How It Works
chatbot.py Overview
This file defines how the chatbot interacts with users and when to:

Answer normally

Call backend functions (e.g., get_tasks_this_week, create_task, etc.)

Perform semantic search via embedded task content

Key Concepts:
Uses google.generativeai for the Gemini API

Each supported function (like get_all_tasks) is declared and callable through Gemini's tool schema

A conversation_histories dictionary stores ongoing chat sessions

Function calls are automatically handled and results are injected back into the chat flow

🔍 Semantic Search
Tasks have their title and description embedded via Gemini Embedding API. These vectors are saved in MongoDB and later used for semantic search when the user asks:

"Are there any tasks related to marketing?"

🧪 Testing the API
You can test the chatbot API using curl like this:
curl -X POST http://localhost:8000/chatbot \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are my tasks this week?",
    "role": "member",
    "user_id": "6627be62c67e2d44cdd032a1"
  }'
You should get a response like:
{
  "response": "You have 3 tasks this week. Here they are:\n1. Finish project report...\n2. Attend team meeting..."
}
🔧 Available Function Calls
Gemini can automatically call the following backend functions:

Function	Description
get_tasks_this_week	Get tasks for this week (filtered by role/user)
get_all_tasks	Get all tasks available
get_user_id_by_name	Convert full name to user ID
create_task	Create a new task with details
list_all_members	List all member users
search_related_tasks	Find tasks relevant to a keyword/topic

🛡️ CORS Config
The server allows cross-origin requests from:
allow_origins=["http://localhost:5173"]  # Vite frontend dev server
You can change this in main.py for production.

📌 Final Notes
Gemini handles multi-turn conversation and function calling seamlessly.

Embedding is task-type aware (e.g., "retrieval_document").

MongoDB must contain a tasks collection with relevant fields for best results.
