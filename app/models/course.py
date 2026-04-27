# ====================================================
#  models/course.py — 코스 관련 테이블 ORM 모델
# ====================================================

from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from app.db import Base


class Course(Base):
    """저장된 코스 테이블"""
    __tablename__ = "course"

    course_id   = Column(String(36),  primary_key=True)
    user_id     = Column(String(36),  ForeignKey("users.user_id"),     nullable=False)
    trip_id     = Column(String(36),  ForeignKey("user_trip.trip_id"), nullable=False)
    course_name = Column(String(50))
    course_type = Column(String(6),   nullable=False)   # AI 또는 CUSTOM
    created_at  = Column(DateTime, default=datetime.utcnow)


class CourseDetail(Base):
    """코스 상세 (일차별 방문 관광지) 테이블"""
    __tablename__ = "course_detail"

    course_detail_id = Column(String(36), primary_key=True)
    course_id        = Column(String(36), ForeignKey("course.course_id"), nullable=False)
    tour_id          = Column(String(36), ForeignKey("tourist.tour_id"),  nullable=False)
    day              = Column(Integer,    nullable=False)
    visit_order      = Column(Integer,    nullable=False)
