import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Create a local test SQLite DB
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_signup_and_login():
    """
    Test registration and subsequent login flow.
    Checks for status codes and matching JSON payloads.
    """
    # 1. Signup user
    response = client.post("/api/auth/signup", json={
        "username": "testvoiceuser",
        "password": "securepassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testvoiceuser"
    assert "id" in data

    # 2. Attempt duplicate signup
    dup_response = client.post("/api/auth/signup", json={
        "username": "testvoiceuser",
        "password": "anotherpassword"
    })
    assert dup_response.status_code == 400

    # 3. Successful login
    login_response = client.post("/api/auth/login", json={
        "username": "testvoiceuser",
        "password": "securepassword123"
    })
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
