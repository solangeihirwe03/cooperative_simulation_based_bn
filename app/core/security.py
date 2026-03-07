from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from jose import jwt,JWTError
from datetime import datetime, timedelta
import os
from app.enums.member import MemberRole

oauth2_scheme =OAuth2PasswordBearer(tokenUrl="login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
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