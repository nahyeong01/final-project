# ====================================================
#  schemas/auth.py — 인증 관련 요청/응답 스키마
# ====================================================

from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    """회원가입 요청 Body"""
    first_name: str
    last_name:  str
    email:      EmailStr
    password:   str
    nation_id:  str
    tel:        Optional[str] = None
    blood_type: Optional[str] = None
    sex:        Optional[str] = None


class LoginRequest(BaseModel):
    """로그인 요청 Body"""
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    """로그인 성공 응답"""
    access_token:  str
    refresh_token: str
    user_id:       str
    first_name:    str
    last_name:     str


class RefreshRequest(BaseModel):
    """토큰 갱신 요청 Body"""
    refresh_token: str


class OAuthRequest(BaseModel):
    """소셜 로그인 요청 Body"""
    oauth_token: str
