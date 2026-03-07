from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from jose import jwt,JWTError
from datetime import datetime, timedelta
import os
from app.enums.member import MemberRole
from sqlalchemy.orm import Session
from app.models.members import Member
from app.db.database import get_db
import hashlib

oauth2_scheme =OAuth2PasswordBearer(tokenUrl="login")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def compare_password(password,hashed_password):
    return pwd_context.verify(password,hashed_password)

def generate_token(data: dict,expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode,os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))

def decode_token(token: str):
    try:
        payload = jwt.decode(token,os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        member_id: str = payload.get("sub")
        if member_id is None:
            raise HTTPException(status_code=401, detail= "Invalid token")
        role: str = payload.get("role", MemberRole.MEMBER.value)
        return {"member_id": member_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
def get_current_user(token: str = Depends(lambda: None), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(token)
    user = db.query(Member).filter(Member.member_id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user