# ====================================================
#  models/accommodation.py — 숙소 관련 테이블 ORM 모델
# ====================================================

from datetime import datetime
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime
from app.db import Base


class AccCategory(Base):
    """숙소 유형 테이블"""
    __tablename__ = "acc_category"

    acc_cat_id   = Column(String(36),  primary_key=True)
    acc_cat_name = Column(String(50),  nullable=False)


class Accommodation(Base):
    """숙소 정보 테이블 (285개)"""
    __tablename__ = "accommodation"

    acc_id     = Column(String(36),  primary_key=True)
    acc_cat_id = Column(String(36),  ForeignKey("acc_category.acc_cat_id"))
    dong_id    = Column(String(8))
    acc_name   = Column(String(200), nullable=False)
    addr       = Column(String(255))
    lat        = Column(Numeric(30, 25))
    lon        = Column(Numeric(30, 25))
    tel        = Column(String(50))
    img_url    = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


class AccommodationWishlist(Base):
    """숙소 찜 목록"""
    __tablename__ = "accommodation_wishlist"

    acc_wish_id = Column(String(36), primary_key=True)
    user_id     = Column(String(36), ForeignKey("users.user_id"),        nullable=False)
    acc_id      = Column(String(36), ForeignKey("accommodation.acc_id"), nullable=False)
    created_at  = Column(DateTime,   default=datetime.utcnow)
