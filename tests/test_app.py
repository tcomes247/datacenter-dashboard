from fastapi.testclient import TestClient
import sys
import os

# Ensure the backend directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

client = TestClient(app)

def test_get_status():
    response = client.get("/status")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert "incidents" in response.json()




