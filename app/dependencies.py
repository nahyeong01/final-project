# ====================================================
#  dependencies.py — JWT 인증 유틸 & 미들웨어
#  토큰 생성 / 검증 함수를 모아놓은 파일
#  라우터에서 Depends(get_current_user)로 인증을 강제할 수 있음
# ====================================================

from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_ACCESS_EXPIRE_HOURS, JWT_REFRESH_EXPIRE_DAYS

# /api/auth/login 엔드포인트를 토큰 발급 URL로 지정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict) -> str:
    """
    Access Token 생성 (기본 24시간 유효)
    data: {"sub": user_id} 형태로 넘기면 됨
    """
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=JWT_ACCESS_EXPIRE_HOURS)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Refresh Token 생성 (기본 7일 유효)
    Access Token 만료 시 새 토큰 발급에 사용
    """
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    요청 헤더의 Bearer 토큰을 검증하고 user_id를 반환
    라우터 함수 파라미터에 user_id: str = Depends(get_current_user) 형태로 사용
    토큰이 없거나 만료되면 자동으로 401 에러 반환
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 토큰이 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception
