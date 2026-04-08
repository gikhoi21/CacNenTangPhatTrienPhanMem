FROM python:3.10-slim

# Đổi tên thư mục làm việc trong container thành /code để tránh trùng tên với folder 'app' của bạn
WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ nội dung từ máy vào /code
COPY . .

EXPOSE 8000

# Chạy uvicorn và chỉ định rõ module
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]