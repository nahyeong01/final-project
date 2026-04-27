# ====================================================
#  models/emergency.py — 긴급대응 관련 테이블 ORM 모델
# ====================================================

from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, ForeignKey, DateTime
from app.db import Base


class Allergy(Base):
    """알레르기 테이블"""
    __tablename__ = "allergy"

    alrg_id   = Column(String(36),  primary_key=True)
    user_id   = Column(String(36),  ForeignKey("users.user_id"), nullable=False)
    alrg_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Medication(Base):
    """복용약 테이블"""
    __tablename__ = "medication"

    med_id    = Column(String(36),  primary_key=True)
    user_id   = Column(String(36),  ForeignKey("users.user_id"), nullable=False)
    med_name  = Column(String(100), nullable=False)
    dsg       = Column(String(30))
    freq      = Column(String(30))
    created_at = Column(DateTime, default=datetime.utcnow)


class UserDisease(Base):
    """기저질환 테이블"""
    __tablename__ = "user_disease"

    user_dis_id   = Column(String(36),  primary_key=True)
    user_id       = Column(String(36),  ForeignKey("users.user_id"), nullable=False)
    user_dis_name = Column(String(100), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)


class EmergencyContact(Base):
    """비상연락처 테이블"""
    __tablename__ = "emergency_contact"

    emrg_contact_id = Column(String(36),  primary_key=True)
    user_id         = Column(String(36),  ForeignKey("users.user_id"), nullable=False)
    contact_name    = Column(String(50),  nullable=False)
    relationship    = Column(String(30))
    tel             = Column(String(20),  nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)


class EmergencyRoom(Base):
    """응급실 위치 정보 테이블"""
    __tablename__ = "emergency_room"

    emrg_room_id   = Column(String(36),  primary_key=True)
    emrg_room_name = Column(String(100), nullable=False)
    lat            = Column(Numeric(30, 25))
    lon            = Column(Numeric(30, 25))
    tel            = Column(String(20))
    note           = Column(Text)
    created_at     = Column(DateTime, default=datetime.utcnow)


class EmergencyRecord(Base):
    """긴급 기록 테이블"""
    __tablename__ = "emergency_record"

    emrg_record_id = Column(String(36),  primary_key=True)
    user_id        = Column(String(36),  ForeignKey("users.user_id"))
    dong_id        = Column(String(8))
    emrg_room_id   = Column(String(36),  ForeignKey("emergency_room.emrg_room_id"))
    lat            = Column(Numeric(30, 25))
    lon            = Column(Numeric(30, 25))
    addr           = Column(String(255))
    addr_src       = Column(String(20))
    msg_txt        = Column(Text)
    created_at     = Column(DateTime, default=datetime.utcnow)
