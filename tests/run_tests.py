import sys
import os

# Add app directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create local test SQLite DB
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

def run():
    print("----------------------------------------")
    print("Running voice platform integration tests...")
    print("----------------------------------------")
    Base.metadata.create_all(bind=engine)
    
    # Check if we can import packages needed
    try:
        import gtts
        print("[Service Check] gTTS: Available")
    except ImportError:
        print("[Service Check] gTTS: NOT Available (will use synthetic beep fallback)")
        
    try:
        import pocket_tts
        print("[Service Check] Pocket TTS: Available")
    except ImportError:
        print("[Service Check] Pocket TTS: NOT Available (will use timbre synthesis fallback)")
        
    client = TestClient(app)
    
    try:
        print("Testing signup endpoint...")
        # 1. Signup user
        response = client.post("/api/auth/signup", json={
            "username": "testvoiceuser",
            "password": "securepassword123"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["username"] == "testvoiceuser"
        print("-> Signup: PASSED")

        # 2. Attempt duplicate signup
        print("Testing duplicate signup prevention...")
        dup_response = client.post("/api/auth/signup", json={
            "username": "testvoiceuser",
            "password": "anotherpassword"
        })
        assert dup_response.status_code == 400, f"Expected 400 for duplicate user, got {dup_response.status_code}"
        print("-> Duplicate Signup Prevention: PASSED")

        # 3. Successful login
        print("Testing login/token generation...")
        login_response = client.post("/api/auth/login", json={
            "username": "testvoiceuser",
            "password": "securepassword123"
        })
        assert login_response.status_code == 200, f"Expected 200, got {login_response.status_code}"
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        print("-> Login & Token Generation: PASSED")
        
        print("----------------------------------------")
        print("All integration tests passed successfully!")
        print("----------------------------------------")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test run encountered error: {e}")
        sys.exit(1)
    finally:
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test.db"):
            try:
                os.remove("./test.db")
            except:
                pass

if __name__ == "__main__":
    run()
