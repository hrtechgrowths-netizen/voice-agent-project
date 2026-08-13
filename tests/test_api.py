import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
import app.main as main_module

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

def test_protected_endpoints_allow_unauthenticated_access(monkeypatch):
    """
    Ensure auth-bypassed endpoints work without Authorization headers.
    """
    monkeypatch.setattr(main_module, "generate_speech", lambda *args, **kwargs: (b"audio", 1.5))
    monkeypatch.setattr(main_module, "clone_voice", lambda *args, **kwargs: (b"audio", 2.0))
    monkeypatch.setattr(main_module, "blend_audio_waveforms", lambda *args, **kwargs: (b"audio", 3.0))
    monkeypatch.setattr(main_module, "upload_audio", lambda *args, **kwargs: "https://example.com/audio.wav")

    tts_response = client.post("/api/tts/generate", json={"text": "hello world"})
    assert tts_response.status_code == 200

    clone_response = client.post(
        "/api/voice-cloning/clone",
        data={"text": "hello world", "voice_name": "demo_voice"},
        files={"reference_file": ("ref.wav", b"sample", "audio/wav")},
    )
    assert clone_response.status_code == 200

    blend_response = client.post(
        "/api/voice-mixing/blend",
        data={"text": "hello world", "voice1": "voice_a", "voice2": "voice_b", "blend_ratio": "0.5"},
    )
    assert blend_response.status_code == 200

    history_response = client.get("/api/history")
    assert history_response.status_code == 200
    assert isinstance(history_response.json(), list)
