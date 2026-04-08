from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from app.database import students_collection, users_collection, db

app = FastAPI()

# Cấu hình CORS để Frontend có thể gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo Collections
grades_collection = db["grades"]
logs_collection = db["logs"]

# --- DATA MODELS ---

class Student(BaseModel):
    name: str
    email: str
    major: str

class User(BaseModel):
    username: str
    password: str

class Grade(BaseModel):
    student_id: str
    subject: str
    score: float = Field(..., ge=0, le=10) # Ràng buộc điểm từ 0 - 10 ở cấp server
    credits: int = Field(..., gt=0)        # Tín chỉ phải lớn hơn 0

# --- HELPER FUNCTIONS ---

async def save_log(action: str, user: str):
    """Lưu nhật ký hoạt động vào MongoDB"""
    logs_collection.insert_one({
        "action": action,
        "user": user,
        "timestamp": datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
    })

# --- AUTH ROUTES ---

@app.post("/register")
async def register(user: User):
    if users_collection.find_one({"username": user.username}):
        return {"status": "error", "message": "Tên đăng nhập đã tồn tại"}
    users_collection.insert_one(user.dict())
    return {"status": "success", "message": "Đăng ký thành công"}

@app.post("/login")
async def login(user: User):
    db_user = users_collection.find_one({"username": user.username, "password": user.password})
    if db_user:
        return {"status": "success", "username": user.username}
    return {"status": "error", "message": "Sai tài khoản hoặc mật khẩu"}

# --- STUDENT ROUTES (QUẢN LÝ SINH VIÊN) ---

@app.get("/students")
async def get_students():
    students = []
    for s in students_collection.find():
        s["id"] = str(s["_id"])
        del s["_id"]
        students.append(s)
    return students

@app.post("/students")
async def add_student(student: Student):
    res = students_collection.insert_one(student.dict())
    await save_log(f"Thêm sinh viên mới: {student.name}", "Admin")
    return {"id": str(res.inserted_id)}

@app.put("/students/{id}")
async def update_student(id: str, student: Student):
    students_collection.update_one({"_id": ObjectId(id)}, {"$set": student.dict()})
    await save_log(f"Cập nhật thông tin sinh viên: {student.name}", "Admin")
    return {"message": "Updated"}

@app.delete("/students/{id}")
async def delete_student(id: str):
    students_collection.delete_one({"_id": ObjectId(id)})
    await save_log("Xóa một sinh viên khỏi hệ thống", "Admin")
    return {"message": "Deleted"}

# --- GRADE ROUTES (QUẢN LÝ ĐIỂM SỐ) ---

@app.get("/grades")
async def get_grades():
    grades = []
    for g in grades_collection.find():
        g["id"] = str(g["_id"])
        del g["_id"]
        grades.append(g)
    return grades

@app.post("/grades")
async def add_grade(grade: Grade):
    grades_collection.insert_one(grade.dict())
    await save_log(f"Nhập điểm môn {grade.subject} cho SV: {grade.student_id}", "Admin")
    return {"status": "success"}

@app.put("/grades/{id}")
async def update_grade(id: str, grade: Grade):
    # Cập nhật điểm dựa trên ID
    result = grades_collection.update_one({"_id": ObjectId(id)}, {"$set": grade.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Grade not found")
    await save_log(f"Chỉnh sửa điểm môn {grade.subject} cho SV: {grade.student_id}", "Admin")
    return {"message": "Updated"}

@app.delete("/grades/{id}")
async def delete_grade(id: str):
    grades_collection.delete_one({"_id": ObjectId(id)})
    await save_log("Xóa một bản ghi điểm số", "Admin")
    return {"message": "Deleted"}

# --- LOG ROUTES (NHẬT KÝ) ---

@app.get("/logs")
async def get_logs():
    # Lấy 10 bản ghi nhật ký mới nhất
    return list(logs_collection.find({}, {"_id": 0}).sort("_id", -1).limit(10))