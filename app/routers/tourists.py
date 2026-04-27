# ====================================================
#  routers/tourists.py — 관광지 & 위시리스트 API
#  GET  /api/tourists               전체 관광지 목록
#  GET  /api/tourists/filtered      제약기반 필터링 (핵심!)
#  GET  /api/tourist-categories     카테고리 목록
#  GET  /api/wishlists/tourists     찜한 관광지 목록
#  POST /api/wishlists/tourists/{tour_id}   찜 추가
#  DELETE /api/wishlists/tourists/{tour_id} 찜 해제
# ====================================================

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.dependencies import get_current_user
from app.models.tourist import (
    Tourist, TouristCategory1, TouristCategory2,
    TouristWishlist
)
from app.services.filter import get_filtered_tourists

router = APIRouter()


# ── 전체 관광지 목록 (제약 필터 미적용) ───────────────

@router.get("/tourists", summary="전체 관광지 목록")
def get_all_tourists(
    tour_cat1_id: Optional[str] = Query(None, description="대분류 ID"),
    tour_cat2_id: Optional[str] = Query(None, description="소분류 ID"),
    keyword:      Optional[str] = Query(None, description="관광지명 검색"),
    page:         int           = Query(0),
    size:         int           = Query(20),
    db:           Session       = Depends(get_db),
    user_id:      str           = Depends(get_current_user),
):
    query = db.query(Tourist)
    if tour_cat2_id:
        query = query.filter(Tourist.tour_cat2_id == tour_cat2_id)
    elif tour_cat1_id:
        cat2_ids = [
            r[0] for r in db.execute(
                text("SELECT tour_cat2_id FROM tourist_category_2 WHERE tour_cat1_id = :id"),
                {"id": tour_cat1_id}
            ).fetchall()
        ]
        if cat2_ids:
            query = query.filter(Tourist.tour_cat2_id.in_(cat2_ids))

    if keyword:
        query = query.filter(Tourist.tour_name.ilike(f"%{keyword}%"))

    total     = query.count()
    tourists  = query.offset(page * size).limit(size).all()

    # 찜 목록 조회 (is_wished 처리)
    wished_ids = {
        r[0] for r in db.execute(
            text("SELECT tour_id FROM tourist_wishlist WHERE user_id = :uid"),
            {"uid": user_id}
        ).fetchall()
    }

    # 카테고리명 매핑
    cat2_map = {c.tour_cat2_id: c for c in db.query(TouristCategory2).all()}
    cat1_map = {c.tour_cat1_id: c for c in db.query(TouristCategory1).all()}

    result = []
    for t in tourists:
        cat2 = cat2_map.get(t.tour_cat2_id)
        cat1 = cat1_map.get(cat2.tour_cat1_id) if cat2 else None
        result.append({
            "tour_id":        t.tour_id,
            "tour_name":      t.tour_name,
            "addr":           t.addr,
            "img_url":        t.img_url,
            "tour_cat1_name": cat1.tour_cat1_name if cat1 else None,
            "tour_cat2_name": cat2.tour_cat2_name if cat2 else None,
            "is_wished":      t.tour_id in wished_ids,
        })

    return {"success": True, "data": {"tourists": result, "total": total}}


# ── 제약기반 관광지 필터링 (핵심 기능!) ───────────────

@router.get("/tourists/filtered", summary="시술 제약 기반 관광지 필터링 ★")
def get_filtered(
    proc_id:      str           = Query(..., description="시술 ID (필수)"),
    tour_cat1_id: Optional[str] = Query(None),
    tour_cat2_id: Optional[str] = Query(None),
    page:         int           = Query(0),
    size:         int           = Query(20),
    db:           Session       = Depends(get_db),
    user_id:      str           = Depends(get_current_user),
):
    result = get_filtered_tourists(
        db=db, proc_id=proc_id, user_id=user_id,
        tour_cat1_id=tour_cat1_id, tour_cat2_id=tour_cat2_id,
        page=page, size=size,
    )
    return {"success": True, "data": result}


# ── 카테고리 목록 ─────────────────────────────────

@router.get("/tourist-categories", summary="관광지 카테고리 (대/소분류)")
def get_tourist_categories(
    parent_id: Optional[str] = Query(None, description="tour_cat1_id, 없으면 대분류 전체"),
    db:        Session       = Depends(get_db),
):
    if parent_id:
        # 소분류 반환
        cats = db.query(TouristCategory2).filter(TouristCategory2.tour_cat1_id == parent_id).all()
        return {"success": True, "data": {"categories": [
            {"id": c.tour_cat2_id, "name": c.tour_cat2_name, "parent_id": c.tour_cat1_id} for c in cats
        ]}}
    else:
        # 대분류 반환
        cats = db.query(TouristCategory1).all()
        return {"success": True, "data": {"categories": [
            {"id": c.tour_cat1_id, "name": c.tour_cat1_name, "parent_id": None} for c in cats
        ]}}


# ── 관광지 위시리스트 ─────────────────────────────

@router.get("/wishlists/tourists", summary="찜한 관광지 목록")
def get_tourist_wishlist(
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    rows = db.execute(
        text("""
            SELECT tw.tour_wish_id, tw.tour_id, tw.created_at,
                   t.tour_name, t.img_url, t.addr,
                   tc1.tour_cat1_name, tc2.tour_cat2_name
            FROM tourist_wishlist tw
            JOIN tourist t          ON tw.tour_id = t.tour_id
            JOIN tourist_category_2 tc2 ON t.tour_cat2_id = tc2.tour_cat2_id
            JOIN tourist_category_1 tc1 ON tc2.tour_cat1_id = tc1.tour_cat1_id
            WHERE tw.user_id = :uid
            ORDER BY tw.created_at DESC
        """),
        {"uid": user_id}
    ).fetchall()

    return {
        "success": True,
        "data": {
            "wishlists": [
                {
                    "tour_wish_id":   r[0],
                    "tour_id":        r[1],
                    "created_at":     str(r[2]),
                    "tour_name":      r[3],
                    "img_url":        r[4],
                    "addr":           r[5],
                    "tour_cat1_name": r[6],
                    "tour_cat2_name": r[7],
                }
                for r in rows
            ]
        }
    }


@router.post("/wishlists/tourists/{tour_id}", status_code=201, summary="관광지 찜 추가")
def add_tourist_wishlist(
    tour_id: str,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    existing = db.query(TouristWishlist).filter_by(user_id=user_id, tour_id=tour_id).first()
    if existing:
        raise HTTPException(409, detail="이미 찜한 관광지입니다.")

    wish = TouristWishlist(
        tour_wish_id=str(uuid.uuid4()),
        user_id=user_id,
        tour_id=tour_id,
    )
    db.add(wish)
    db.commit()
    return {"success": True, "data": {"tour_wish_id": wish.tour_wish_id}}


@router.delete("/wishlists/tourists/{tour_id}", summary="관광지 찜 해제")
def remove_tourist_wishlist(
    tour_id: str,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    wish = db.query(TouristWishlist).filter_by(user_id=user_id, tour_id=tour_id).first()
    if not wish:
        raise HTTPException(404, detail="찜 항목을 찾을 수 없습니다.")
    db.delete(wish)
    db.commit()
    return {"success": True, "data": {"message": "Removed"}}
