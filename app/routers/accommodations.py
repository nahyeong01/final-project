# ====================================================
#  routers/accommodations.py — 숙소 API
#  GET /api/accommodations     숙소 목록 (반경/자치구/유형 필터)
#  GET /api/acc-categories     숙소 유형 목록
#  POST/DELETE /api/wishlists/accommodations/{acc_id}  찜
# ====================================================

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.dependencies import get_current_user
from app.models.accommodation import Accommodation, AccCategory, AccommodationWishlist
from app.models.hospital import Hospital
from app.services.haversine import haversine

router = APIRouter()


@router.get("/accommodations", summary="숙소 목록 조회")
def get_accommodations(
    hosp_id:    Optional[str]   = Query(None,  description="기준 병원 ID (반경 계산용)"),
    radius_km:  float           = Query(1.0,   description="반경 km (0.5 | 1 | 3)"),
    gu_id:      Optional[str]   = Query(None,  description="자치구 ID"),
    acc_cat_id: Optional[str]   = Query(None,  description="숙소 유형 ID"),
    page:       int             = Query(0),
    size:       int             = Query(20),
    db:         Session         = Depends(get_db),
    user_id:    str             = Depends(get_current_user),
):
    query = db.query(Accommodation)

    if acc_cat_id:
        query = query.filter(Accommodation.acc_cat_id == acc_cat_id)

    accs = query.all()

    # 병원 기준 반경 필터링 (Haversine)
    hosp_lat, hosp_lon = None, None
    if hosp_id:
        hosp = db.query(Hospital).filter(Hospital.hosp_id == hosp_id).first()
        if hosp and hosp.lat and hosp.lon:
            hosp_lat = float(hosp.lat)
            hosp_lon = float(hosp.lon)

    cat_map = {c.acc_cat_id: c.acc_cat_name for c in db.query(AccCategory).all()}

    result = []
    for a in accs:
        acc_lat = float(a.lat) if a.lat else None
        acc_lon = float(a.lon) if a.lon else None

        distance_km = None
        if hosp_lat and acc_lat:
            distance_km = haversine(hosp_lat, hosp_lon, acc_lat, acc_lon)
            if distance_km > radius_km:
                continue   # 반경 밖 제외

        result.append({
            "acc_id":       a.acc_id,
            "acc_name":     a.acc_name,
            "addr":         a.addr,
            "lat":          acc_lat,
            "lon":          acc_lon,
            "tel":          a.tel,
            "img_url":      a.img_url,
            "acc_cat_name": cat_map.get(a.acc_cat_id),
            "distance_km":  distance_km,
        })

    # 거리 기준 정렬
    result.sort(key=lambda x: x["distance_km"] if x["distance_km"] is not None else 999)

    total       = len(result)
    paginated   = result[page * size: (page + 1) * size]

    return {"success": True, "data": {"accommodations": paginated, "total": total}}


@router.get("/acc-categories", summary="숙소 유형 목록")
def get_acc_categories(db: Session = Depends(get_db)):
    cats = db.query(AccCategory).all()
    return {"success": True, "data": {"categories": [
        {"acc_cat_id": c.acc_cat_id, "acc_cat_name": c.acc_cat_name} for c in cats
    ]}}


@router.post("/wishlists/accommodations/{acc_id}", status_code=201, summary="숙소 찜 추가")
def add_acc_wishlist(
    acc_id:  str,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    existing = db.query(AccommodationWishlist).filter_by(user_id=user_id, acc_id=acc_id).first()
    if existing:
        raise HTTPException(409, detail="이미 찜한 숙소입니다.")
    wish = AccommodationWishlist(acc_wish_id=str(uuid.uuid4()), user_id=user_id, acc_id=acc_id)
    db.add(wish)
    db.commit()
    return {"success": True, "data": {"acc_wish_id": wish.acc_wish_id}}


@router.delete("/wishlists/accommodations/{acc_id}", summary="숙소 찜 해제")
def remove_acc_wishlist(
    acc_id:  str,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    wish = db.query(AccommodationWishlist).filter_by(user_id=user_id, acc_id=acc_id).first()
    if not wish:
        raise HTTPException(404, detail="찜 항목을 찾을 수 없습니다.")
    db.delete(wish)
    db.commit()
    return {"success": True, "data": {"message": "Removed"}}
