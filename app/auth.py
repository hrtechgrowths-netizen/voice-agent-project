# ==========================================
# FIXED: Missing Development User Function
# ==========================================
def get_or_create_development_user(db):
    """
    Finds the default development user in the database.
    If it doesn't exist, it creates one automatically.
    """
    from app.models import User
    from datetime import datetime
    
    # Check if the dev_user already exists
    dev_user = db.query(User).filter(User.username == "dev_user").first()
    
    if not dev_user:
        # Create a default dummy password hash
        # If your auth file uses a specific hasher, ensure it matches
        dev_user = User(
            username="dev_user", 
            hashed_password="development_mode_secured_bypass_hash"
        )
        db.add(dev_user)
        db.commit()
        db.refresh(dev_user)
        print("Successfully created a new development user profile.")
        
    return dev_user

