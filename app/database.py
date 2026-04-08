import os
from pymongo import MongoClient

# Docker sẽ truyền biến MONGO_URL vào, nếu chạy máy thường nó sẽ lấy mặc định là localhost
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongodb:27017/")

client = MongoClient(MONGO_URL)
db = client["student_db"]

# Các collection
students_collection = db["students"]
users_collection = db["users"]