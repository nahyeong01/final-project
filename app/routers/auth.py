# ====================================================
#  routers/auth.py — 인증 API
#  POST /api/auth/register  회원가입
#  POST /api/auth/login     로그인
#  POST /api/auth/refresh   토큰 갱신
#  POST /api/auth/logout    로그아웃
# ====================================================

import uuid
import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest, LoginRequest, RefreshRequest, OAuthRequest
)
from app.dependencies import (
    create_access_token, create_refresh_token, get_current_user
)
from app.config import JWT_SECRET, JWT_ALGORITHM
from jose import JWTError, jwt

router = APIRouter()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hashlib.sha256(plain.encode()).hexdigest() == hashed


@router.post("/register", status_code=201, summary="회원가입")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(409, detail="이미 사용 중인 이메일입니다.")

    new_user = User(
        user_id    = str(uuid.uuid4()),
        first_name = req.first_name,
        last_name  = req.last_name,
        email      = req.email,
        password   = hash_password(req.password),
        nation_id  = req.nation_id,
        tel        = req.tel,
        blood_type = req.blood_type,
        sex        = req.sex,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "success": True,
        "data": {
            "user_id":    new_user.user_id,
            "email":      new_user.email,
            "first_name": new_user.first_name,
            "last_name":  new_user.last_name,
            "created_at": str(new_user.created_at),
        }
    }


@router.post("/login", summary="로그인 → JWT 발급")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()

    if not user or not verify_password(req.password, user.password):
        raise HTTPException(401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    access  = create_access_token({"sub": user.user_id})
    refresh = create_refresh_token({"sub": user.user_id})

    return {
        "success": True,
        "data": {
            "access_token":  access,
            "refresh_token": refresh,
            "user_id":       user.user_id,
            "first_name":    user.first_name,
            "last_name":     user.last_name,
        }
    }


@router.post("/refresh", summary="Access Token 갱신")
def refresh_token(req: RefreshRequest):
    try:
        payload = jwt.decode(req.refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, detail="유효하지 않은 Refresh Token입니다.")
    except JWTError:
        raise HTTPException(401, detail="Refresh Token이 만료되었거나 유효하지 않습니다.")

    new_access = create_access_token({"sub": user_id})
    return {"success": True, "data": {"access_token": new_access}}


@router.post("/logout", summary="로그아웃")
def logout(user_id: str = Depends(get_current_user)):
    return {"success": True, "data": {"message": "Logged out"}}


@router.post("/oauth/{provider}", summary="소셜 로그인 (google / apple)")
def oauth_login(provider: str, req: OAuthRequest, db: Session = Depends(get_db)):
    raise HTTPException(501, detail="소셜 로그인은 추후 구현 예정입니다.")
