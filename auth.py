import uuid
import time
from typing import List

from fastapi import HTTPException, Response, Depends, Request
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from model import User
from sql_connect import get_db


class AuthService:
    @staticmethod
    def register_user(user_data: dict, db_session: Session):
        """Đăng ký người dùng mới"""
        if db_session.query(User).filter(User.code == user_data["code"]).first():
            raise HTTPException(status_code=400, detail="User code already exists")

        hashed_password = bcrypt.hash(user_data["password"])

        new_user = User(
            code=user_data["code"],
            email=user_data.get("email", None) if user_data.get("email") != "" else None,
            role=user_data.get("role", "user"),
            password=hashed_password,
            semester=user_data.get("semester", None),
        )
        db_session.add(new_user)
        db_session.commit()

        return {"message": "User registered successfully"}

    @staticmethod
    def login_user(login_data: dict, response: Response, db_session: Session):
        """Đăng nhập người dùng"""
        user = db_session.query(User).filter(User.code == login_data["code"]).first()
        if not user or not bcrypt.verify(login_data["password"], user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        session_id = str(uuid.uuid4())
        user.session = session_id
        user.updated_at = time.time()
        db_session.commit()

        response.set_cookie(key="session_id", value=session_id, httponly=True)

        return {
            "message": "Login successful",
            "user": {
                "code": user.code,
                "role": user.role,
                "semester": user.semester,
            },
        }

    @staticmethod
    def logout_user(response: Response, db_session: Session, session_id: str):
        """Đăng xuất người dùng"""
        user = db_session.query(User).filter(User.session == session_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid session")

        user.session = None
        db_session.commit()

        response.delete_cookie(key="session_id")

        return {"message": "Logout successful"}

    @staticmethod
    def verify_session(session_id: str, db_session: Session):
        """Xác thực session người dùng"""
        user = db_session.query(User).filter(User.session == session_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        return {
            "message": "Session is valid",
            "user": {
                "code": user.code,
                "role": user.role,
                "semester": user.semester,
                "id": user.uuid,
            },
        }