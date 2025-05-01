# create_embed_task.py
from mongo_utils import update_task_embeddings
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    print("Starting embedding update...")
    update_task_embeddings()
    print("Embedding update completed.")