from datetime import datetime, timedelta
import pymongo
from bson import ObjectId 
import os
from dotenv import load_dotenv
from embed_utils import generate_embedding
from rank_bm25 import BM25Okapi

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
            "priority": task["priority"],
            "description": task["description"],
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
            "priority": task["priority"],
            "description": task["description"],
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

def create_task(title: str, description: str, assigned_to_id: str, due_date_str: str, created_by_id: str, priority: str = "Medium", todo_checklist: list = []) -> dict:
    """
    Tạo task mới và lưu vào MongoDB.
    - `assigned_to_id`: _id của người dùng được giao (string)
    - `created_by_id`: _id của người tạo task (string)
    - `due_date_str`: ngày hết hạn ở định dạng 'YYYY-MM-DD'
    - `priority`: Low, Medium, High
    - `todo_checklist`: Danh sách các công việc cần làm trong task, mỗi checklist có cấu trúc text và completed.
    """
    try:
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Ngày deadline không đúng định dạng. Dùng 'YYYY-MM-DD'.")

    if not todo_checklist:
        raise ValueError("Danh sách todoChecklist không thể trống.")

    # Kiểm tra cấu trúc todoChecklist
    for item in todo_checklist:
        if "text" not in item or "completed" not in item:
            raise ValueError("Mỗi phần tử trong todoChecklist phải có trường 'text' và 'completed'.")
        if not isinstance(item["completed"], bool):
            raise ValueError("Trường 'completed' trong todoChecklist phải là kiểu boolean.")
    
    task = {
        "title": title,
        "description": description,
        "assignedTo": [ObjectId(assigned_to_id)],  # Giao task cho người dùng
        "createdBy": ObjectId(created_by_id),     # Người tạo task
        "dueDate": due_date,
        "status": "Pending",  # default
        "priority": priority,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "attachments": [],    # Mảng trống cho file đính kèm
        "todoChecklist": todo_checklist,  # Danh sách công việc cần làm trong task
        "progress": 0         # Tiến độ mặc định là 0%
    }

    result = collection.insert_one(task)
    return {"message": "Task created successfully", "task_id": str(result.inserted_id)}



def list_all_members() -> list:
    """
    Trả về danh sách tất cả người dùng có role là 'member'.
    """
    users = list(db["users"].find({"role": "member"}))

    return [
        {
            "user_id": str(user["_id"]),
            "name": user["name"]
        }
        for user in users
    ]

def get_task_text(task: dict) -> str:
    """
    Trả về văn bản mô tả của task. (title + description)
    """
    title = task.get("title", "")
    description = task.get("description", "")
    return f"{title} {description}"
    

def update_task_embeddings():
    tasks = collection.find({"embedding": {"$exists": False}})
    for task in tasks:
        embedding = generate_embedding(get_task_text(task), task_type="RETRIEVAL_DOCUMENT")
        collection.update_one({"_id": task["_id"]}, {"$set": {"embedding": embedding}})

def search_similar_tasks(query_embedding: list, limit: int = 3) -> list:
    pipeline = [
        {
            "$vectorSearch": {
                "index": "task_embedding_vector_index",  # Tên index cần tạo trong MongoDB Atlas
                "path": "embedding",
                "queryVector": query_embedding,
                "limit": limit,
                "numCandidates": 3
            }
        },
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "description": 1,
                "dueDate": 1,
                "status": 1,
                "assignedTo": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    results = list(collection.aggregate(pipeline))
    return results

def get_user_names(user_ids: list) -> list:
    """
    Trả về danh sách tên người dùng từ danh sách ObjectId.
    """
    users = list(db["users"].find({"_id": {"$in": [ObjectId(uid) for uid in user_ids]}}))
    return [user["name"] for user in users]

def rerank_with_bm25(query: str, tasks: list) -> list:
    corpus = [get_task_text(task) for task in tasks]
    tokenized_corpus = [doc.split() for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.split()
    scores = bm25.get_scores(tokenized_query)
    
    for i, task in enumerate(tasks):
        task["bm25_score"] = scores[i]
    
    # Kết hợp score bằng cách cho trọng số hoặc chuẩn hóa
    for task in tasks:
        # normalize if needed
        combined_score = 0.5 * task.get("score", 0) + 0.5 * task["bm25_score"]
        task["combined_score"] = combined_score
    
    # Sắp xếp lại theo combined score
    tasks.sort(key=lambda x: x["combined_score"], reverse=True)
    return tasks

def search_related_tasks(query: str) -> dict:
    query_embedding = generate_embedding(query, task_type="RETRIEVAL_QUERY")
    similar_tasks = search_similar_tasks(query_embedding)
    reranked_tasks = rerank_with_bm25(query, similar_tasks)

    task_list = [
        {
            "title": task["title"],
            "description": task["description"],
            "score": task["score"],
            "dueDate": task["dueDate"].strftime("%Y-%m-%d"),
            "status": task["status"],
            "assignedTo": get_user_names(task["assignedTo"])
        }
        for task in reranked_tasks
    ]

    return {"tasks": task_list}


