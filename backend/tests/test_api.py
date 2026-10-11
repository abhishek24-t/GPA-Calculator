import pytest
import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["calculation_engine"] == "deterministic_python_v1"


def test_api_calculate_sgpa():
    payload = {
        "subjects": [
            {"name": "Engineering Maths I", "credit": 4.0, "grade": "O"},
            {"name": "Engineering Physics", "credit": 4.0, "grade": "A+"},
            {"name": "Basic Electrical", "credit": 3.0, "grade": "A"}
        ]
    }
    response = client.post("/api/calculate/sgpa", json=payload)
    assert response.status_code == 200
    data = response.json()
    # 4*10 + 4*9 + 3*8 = 40 + 36 + 24 = 100 / 11 = 9.09
    assert data["sgpa"] == 9.09
    assert data["total_credits"] == 11.0


def test_api_calculate_cgpa():
    payload = {
        "semesters": [
            {"name": "Semester 1", "sgpa": 8.0, "credits": 20.0},
            {"name": "Semester 2", "sgpa": 9.0, "credits": 20.0}
        ]
    }
    response = client.post("/api/calculate/cgpa", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["cgpa"] == 8.5
    assert data["total_credits"] == 40.0


def test_api_predict_target_gpa():
    payload = {
        "current_cgpa": 7.5,
        "completed_credits": 60.0,
        "remaining_credits": 20.0,
        "target_cgpa": 8.0
    }
    response = client.post("/api/predict/target-gpa", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["achievable"] is True
    assert data["required_sgpa"] == 9.5


def test_api_history_crud():
    # 1. Get initial history (sample data)
    res = client.get("/api/history")
    assert res.status_code == 200
    initial_items = res.json()
    assert len(initial_items) >= 1

    # 2. Create new record
    new_record = {
        "record_type": "semester",
        "title": "Test Semester 5",
        "semester_num": 5,
        "sgpa": 8.75,
        "cgpa": 8.50,
        "credits": 22.0,
        "data": {"subjects": [{"name": "Web Dev", "credit": 3.0, "grade": "O"}]}
    }
    create_res = client.post("/api/history", json=new_record)
    assert create_res.status_code == 201
    created = create_res.json()
    rec_id = created["id"]
    assert created["title"] == "Test Semester 5"

    # 3. Update record
    update_res = client.put(f"/api/history/{rec_id}", json={"title": "Updated Semester 5", "sgpa": 9.0})
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Semester 5"
    assert update_res.json()["sgpa"] == 9.0

    # 4. Delete record
    del_res = client.delete(f"/api/history/{rec_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True


def test_api_chat():
    payload = {
        "message": "What is my SGPA if I have Math 4 credits A+, Physics 4 credits A?",
        "conversation_id": "test_conv"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 10
