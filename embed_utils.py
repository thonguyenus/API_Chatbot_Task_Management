# embed_utils.py
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

def generate_embedding(text: str, task_type: str) -> list:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    result = client.models.embed_content(
        model="gemini-embedding-exp-03-07",
        contents=[text],
        config=types.EmbedContentConfig(task_type=task_type)
    )
    embedding = list(float(x) for x in result.embeddings[0].values)
    return embedding