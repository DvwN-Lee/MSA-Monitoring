from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import User
import os

app = FastAPI(title="User Service")

# 앱 시작 시 테이블 생성
Base.metadata.create_all(bind=engine)

@app.post("/users")
def create_user(username: str, email: str, password: str, db: Session = Depends(get_db)):
    # 중복 체크
    existing = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # 비밀번호 해싱 (실제로는 bcrypt 사용)
    hashed_password = f"hashed_{password}"
    
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"id": user.id, "username": user.username, "email": user.email}

@app.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "email": u.email} for u in users]

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "user-service"}

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    try:
        user_count = db.query(User).count()
        return {
            "service": "user-service",
            "healthy": True,
            "database": {
                "status": "online",
                "user_count": user_count
            }
        }
    except Exception as e:
        return {
            "service": "user-service",
            "healthy": False,
            "database": {"status": "offline", "error": str(e)}
        }