# ====================================================
#  models/user.py — 사용자 관련 테이블 ORM 모델
#  users, nationality, user_trip, user_hospital_procedure
# ====================================================

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from app.db import Base


class Nationality(Base):
    """국적 코드 테이블 (164개국)"""
    __tablename__ = "nationality"

    nation_id   = Column(String(3),   primary_key=True)
    nation_name = Column(String(100), nullable=False)


class User(Base):
    """회원 정보 테이블"""
    __tablename__ = "users"

    user_id    = Column(String(36),  primary_key=True)
    nation_id  = Column(String(3),   ForeignKey("nationality.nation_id"), nullable=False)
    first_name = Column(String(50),  nullable=False)
    last_name  = Column(String(50),  nullable=False)
    id         = Column(String(255))
    password   = Column(String(255))
    email      = Column(String(100), nullable=False, unique=True)
    tel        = Column(String(20))
    blood_type = Column(String(3))
    sex        = Column(String(1))
    created_at = Column(DateTime, default=datetime.utcnow)


class UserTrip(Base):
    """여행 일정 테이블"""
    __tablename__ = "user_trip"

    trip_id    = Column(String(36), primary_key=True)
    user_id    = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    trip_start = Column(DateTime,   nullable=False)
    trip_end   = Column(DateTime,   nullable=False)
    created_at = Column(DateTime,   default=datetime.utcnow)


class UserHospitalProcedure(Base):
    """유저가 선택한 시술-병원 연결 테이블"""
    __tablename__ = "user_hospital_procedure"

    user_hosp_proc_id = Column(String(36), primary_key=True)
    user_id           = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    hosp_proc_id      = Column(String(36))   # null 허용 → 병원 건너뛰기 대응
    created_at        = Column(DateTime, default=datetime.utcnow)
