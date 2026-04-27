# ====================================================
#  schemas/tourist.py — 관광지 관련 요청/응답 스키마
# ====================================================

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TouristItem(BaseModel):
    """관광지 카드 아이템"""
    tour_id:        str
    tour_name:      str
    addr:           Optional[str]
    img_url:        Optional[str]
    tour_cat1_name: Optional[str]
    tour_cat2_name: Optional[str]
    is_wished:      bool = False


class FilteredTouristResponse(BaseModel):
    """제약기반 관광지 필터링 응답"""
    tourists:         List[TouristItem]
    total:            int
    applied_cautions: List[str]   # 적용된 주의사항 태그명 목록 (배너 표시용)


class WishlistItem(BaseModel):
    """찜한 관광지 아이템"""
    tour_wish_id:   str
    tour_id:        str
    tour_name:      str
    img_url:        Optional[str]
    tour_cat1_name: Optional[str]
    tour_cat2_name: Optional[str]
    created_at:     Optional[datetime]


class CategoryItem(BaseModel):
    """관광지 카테고리 아이템"""
    id:        str
    name:      str
    parent_id: Optional[str] = None
