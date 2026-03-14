from fastapi import Depends, HTTPException
from app.db.database import SessionLocal
from app.core.security import get_current_user

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_role(role: str):
    def role_checker(current_user=Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(status_code=403, detail="Not authorized")
        return current_user
    return role_checker