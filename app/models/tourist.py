# ====================================================
#  models/tourist.py — 관광지 관련 테이블 ORM 모델
# ====================================================

from datetime import datetime
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Float
from app.db import Base


class TouristCategory1(Base):
    """관광지 대분류 테이블"""
    __tablename__ = "tourist_category_1"

    tour_cat1_id   = Column(String(36),  primary_key=True)
    tour_cat1_name = Column(String(50),  nullable=False)


class TouristCategory2(Base):
    """관광지 소분류 테이블"""
    __tablename__ = "tourist_category_2"

    tour_cat2_id   = Column(String(36),  primary_key=True)
    tour_cat1_id   = Column(String(36),  ForeignKey("tourist_category_1.tour_cat1_id"))
    tour_cat2_name = Column(String(50),  nullable=False)


class Tourist(Base):
    """관광지 정보 테이블 (10,165개)"""
    __tablename__ = "tourist"

    tour_id      = Column(String(36),  primary_key=True)
    tour_cat2_id = Column(String(36),  ForeignKey("tourist_category_2.tour_cat2_id"))
    dong_id      = Column(String(8))
    tour_name    = Column(String(300), nullable=False)
    addr         = Column(String(255))
    lat          = Column(Numeric(30, 25))
    lon          = Column(Numeric(30, 25))
    img_url      = Column(String(500))
    created_at   = Column(DateTime, default=datetime.utcnow)


class TouristCaution(Base):
    """관광지-주의사항 매핑 테이블"""
    __tablename__ = "tourist_caution"

    tour_caut_id      = Column(String(36), primary_key=True)
    tour_id           = Column(String(36), ForeignKey("tourist.tour_id"))
    after_caut_tag_id = Column(String(36), ForeignKey("after_caution_tag.after_caut_tag_id"))


class TouristWishlist(Base):
    """관광지 찜 목록"""
    __tablename__ = "tourist_wishlist"

    tour_wish_id = Column(String(36), primary_key=True)
    user_id      = Column(String(36), ForeignKey("users.user_id"),   nullable=False)
    tour_id      = Column(String(36), ForeignKey("tourist.tour_id"), nullable=False)
    created_at   = Column(DateTime,   default=datetime.utcnow)


class ProcRecommendationCache(Base):
    """같은 시술 받은 유저 행동 기반 관광지 추천 점수"""
    __tablename__ = "proc_recommedation_cache"

    proc_rec_id = Column(String(255), primary_key=True)
    proc_id     = Column(String(36),  ForeignKey("medical_procedure.proc_id"))
    tour_id     = Column(String(36),  ForeignKey("tourist.tour_id"))
    score_p     = Column(Float)
    rank_p      = Column(Float)


class NationRecommendationCache(Base):
    """같은 국적 유저 행동 기반 관광지 추천 점수"""
    __tablename__ = "nation_recommendation_cache"

    nation_rec_id = Column(String(255), primary_key=True)
    nation_id     = Column(String(3),   ForeignKey("nationality.nation_id"))
    tour_id       = Column(String(36),  ForeignKey("tourist.tour_id"))
    score_a       = Column(Float)
    rank_a        = Column(Float)
