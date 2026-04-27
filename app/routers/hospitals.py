# ====================================================
#  routers/hospitals.py — 병원 & 시술 API
#  GET /api/hospitals              병원 목록 (필터)
#  GET /api/hospitals/{hosp_id}    병원 상세
#  POST/DELETE /api/wishlists/hospitals/{hosp_id}  병원 찜
#  GET /api/medical-procedures     시술 목록
#  GET /api/medical-procedures/{proc_id} 시술 상세
#  GET /api/medical-depts          진료과 목록
#  GET /api/nationalities          국적 목록
#  GET /api/regions/gu             서울 자치구 목록
# ====================================================

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.dependencies import get_current_user
from app.models.hospital import (
    Hospital, HospitalDept, MedicalDept, HospitalProcedure, MedicalProcedure,
    HospitalServiceLang, ServiceLang, HospitalWishlist
)
from app.models.user import Nationality

router = APIRouter()


# ── 병원 목록 ─────────────────────────────────────

@router.get("/hospitals", summary="병원 목록 조회 (필터)")
def get_hospitals(
    gu_id:        Optional[str] = Query(None, description="자치구 ID"),
    proc_id:      Optional[str] = Query(None, description="시술 ID"),
    medi_dept_id: Optional[str] = Query(None, description="진료과 ID"),
    kahf:         Optional[int] = Query(None, description="우수인증 여부 0/1"),
    page:         int           = Query(0,    description="페이지 번호 (0부터 시작)"),
    size:         int           = Query(20,   description="한 페이지 당 개수"),
    db:           Session       = Depends(get_db),
    user_id:      str           = Depends(get_current_user),
):
    query = db.query(Hospital)
    if kahf is not None:
        query = query.filter(Hospital.kahf == kahf)

    # gu_id 필터 (dong_id → sigungu → gu_id 역참조)
    # 간단하게는 addr LIKE 로 처리 가능하나 정확도를 위해 subquery 권장
    # TODO: sigungu 테이블 연동 후 정밀 필터링 구현

    # proc_id 필터 (hospital_procedure 조인)
    if proc_id:
        hosp_ids = [
            r[0] for r in db.execute(
                text("SELECT DISTINCT hosp_id FROM hospital_procedure WHERE proc_id = :p"),
                {"p": proc_id}
            ).fetchall()
        ]
        if hosp_ids:
            query = query.filter(Hospital.hosp_id.in_(hosp_ids))
        else:
            return {"success": True, "data": {"hospitals": [], "total": 0}}

    # medi_dept_id 필터
    if medi_dept_id:
        hosp_ids_by_dept = [
            r[0] for r in db.execute(
                text("SELECT DISTINCT hosp_id FROM hospital_dept WHERE medi_dept_id = :d"),
                {"d": medi_dept_id}
            ).fetchall()
        ]
        if hosp_ids_by_dept:
            query = query.filter(Hospital.hosp_id.in_(hosp_ids_by_dept))
        else:
            return {"success": True, "data": {"hospitals": [], "total": 0}}

    total = query.count()
    hospitals = query.offset(page * size).limit(size).all()

    result = []
    for h in hospitals:
        # 진료과명 조회
        dept_names = [
            r[0] for r in db.execute(
                text("""
                    SELECT md.medi_dept_name FROM hospital_dept hd
                    JOIN medical_dept md ON hd.medi_dept_id = md.medi_dept_id
                    WHERE hd.hosp_id = :id
                """), {"id": h.hosp_id}
            ).fetchall()
        ]
        # 시술명 조회
        proc_names = [
            r[0] for r in db.execute(
                text("""
                    SELECT mp.proc_name FROM hospital_procedure hp
                    JOIN medical_procedure mp ON hp.proc_id = mp.proc_id
                    WHERE hp.hosp_id = :id
                """), {"id": h.hosp_id}
            ).fetchall()
        ]
        # 외국어 서비스 조회
        lang_names = [
            r[0] for r in db.execute(
                text("""
                    SELECT sl.svc_lang_name FROM hospital_service_lang hsl
                    JOIN service_lang sl ON hsl.svc_lang_id = sl.svc_lang_id
                    WHERE hsl.hosp_id = :id
                """), {"id": h.hosp_id}
            ).fetchall()
        ]

        result.append({
            "hosp_id":        h.hosp_id,
            "hosp_name":      h.hosp_name,
            "addr":           h.addr,
            "lat":            float(h.lat) if h.lat else None,
            "lon":            float(h.lon) if h.lon else None,
            "kahf":           h.kahf,
            "coordinator":    h.coordinator,
            "medi_dept_names": dept_names,
            "proc_names":     proc_names,
            "svc_lang_names": lang_names,
        })

    return {"success": True, "data": {"hospitals": result, "total": total}}


# ── 병원 상세 ─────────────────────────────────────

@router.get("/hospitals/{hosp_id}", summary="병원 상세 조회")
def get_hospital_detail(
    hosp_id: str,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    h = db.query(Hospital).filter(Hospital.hosp_id == hosp_id).first()
    if not h:
        raise HTTPException(404, detail="병원을 찾을 수 없습니다.")

    depts = db.execute(
        text("SELECT md.medi_dept_id, md.medi_dept_name FROM hospital_dept hd JOIN medical_dept md ON hd.medi_dept_id = md.medi_dept_id WHERE hd.hosp_id = :id"),
        {"id": hosp_id}
    ).fetchall()

    procs = db.execute(
        text("SELECT mp.proc_id, mp.proc_name FROM hospital_procedure hp JOIN medical_procedure mp ON hp.proc_id = mp.proc_id WHERE hp.hosp_id = :id"),
        {"id": hosp_id}
    ).fetchall()

    langs = db.execute(
        text("SELECT sl.svc_lang_id, sl.svc_lang_name FROM hospital_service_lang hsl JOIN service_lang sl ON hsl.svc_lang_id = sl.svc_lang_id WHERE hsl.hosp_id = :id"),
        {"id": hosp_id}
    ).fetchall()

    return {
        "success": True,
        "data": {
            "hosp_id":       h.hosp_id,
            "hosp_name":     h.hosp_name,
            "addr":          h.addr,
            "lat":           float(h.lat) if h.lat else None,
            "lon":           float(h.lon) if h.lon else None,
            "hosp_url":      h.hosp_url,
            "kahf":          h.kahf,
            "coordinator":   h.coordinator,
            "online_reserv": h.online_reserv,
            "facility_info": h.facility_info,
            "history":       h.history,
            "sns_url":       h.sns_url,
            "medi_depts":    [{"medi_dept_id": r[0], "medi_dept_name": r[1]} for r in depts],
            "procedures":    [{"proc_id": r[0], "proc_name": r[1]} for r in procs],
            "service_langs": [{"svc_lang_id": r[0], "svc_lang_name": r[1]} for r in langs],
        }
    }


# ── 병원 찜 ──────────────────────────────────────

@router.post("/wishlists/hospitals/{hosp_id}", status_code=201, summary="병원 찜 추가")
def add_hospital_wishlist(
    hosp_id: str,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    existing = db.query(HospitalWishlist).filter_by(user_id=user_id, hosp_id=hosp_id).first()
    if existing:
        raise HTTPException(409, detail="이미 찜한 병원입니다.")
    wish = HospitalWishlist(hosp_wish_id=str(uuid.uuid4()), user_id=user_id, hosp_id=hosp_id)
    db.add(wish)
    db.commit()
    return {"success": True, "data": {"hosp_wish_id": wish.hosp_wish_id}}


@router.delete("/wishlists/hospitals/{hosp_id}", summary="병원 찜 해제")
def remove_hospital_wishlist(
    hosp_id: str,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    wish = db.query(HospitalWishlist).filter_by(user_id=user_id, hosp_id=hosp_id).first()
    if not wish:
        raise HTTPException(404, detail="찜 항목을 찾을 수 없습니다.")
    db.delete(wish)
    db.commit()
    return {"success": True, "data": {"message": "Removed"}}


# ── 시술 ─────────────────────────────────────────

@router.get("/medical-procedures", summary="시술 목록")
def get_procedures(
    medi_dept_id: Optional[str] = Query(None),
    db:           Session       = Depends(get_db),
    user_id:      str           = Depends(get_current_user),
):
    query = db.query(MedicalProcedure)
    if medi_dept_id:
        query = query.filter(MedicalProcedure.medi_dept_id == medi_dept_id)

    procs = query.all()
    dept_map = {d.medi_dept_id: d.medi_dept_name for d in db.query(MedicalDept).all()}

    return {
        "success": True,
        "data": {
            "procedures": [
                {
                    "proc_id":       p.proc_id,
                    "proc_name":     p.proc_name,
                    "medi_dept_id":  p.medi_dept_id,
                    "medi_dept_name": dept_map.get(p.medi_dept_id),
                }
                for p in procs
            ]
        }
    }


@router.get("/medical-procedures/{proc_id}", summary="시술 상세 정보")
def get_procedure_detail(
    proc_id: str,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    p = db.query(MedicalProcedure).filter(MedicalProcedure.proc_id == proc_id).first()
    if not p:
        raise HTTPException(404, detail="시술 정보를 찾을 수 없습니다.")

    return {
        "success": True,
        "data": {
            "proc_id":      p.proc_id,
            "proc_name":    p.proc_name,
            "proc_desc":    p.proc_desc,
            "before_caut":  p.before_caut,
            "after_note":   p.after_note,
            "after_caut":   p.after_caut,
            "side_eff":     p.side_eff,
            "hosp_req_sym": p.hosp_req_sym,
        }
    }


# ── 진료과 ────────────────────────────────────────

@router.get("/medical-depts", summary="진료과 목록")
def get_medical_depts(db: Session = Depends(get_db)):
    depts = db.query(MedicalDept).all()
    return {"success": True, "data": {"depts": [
        {"medi_dept_id": d.medi_dept_id, "medi_dept_name": d.medi_dept_name} for d in depts
    ]}}


# ── 공통 코드 (병원 라우터에 함께 관리) ──────────────

@router.get("/nationalities", summary="국적 목록 (164개국)")
def get_nationalities(db: Session = Depends(get_db)):
    items = db.query(Nationality).all()
    return {"success": True, "data": {"nationalities": [
        {"nation_id": n.nation_id, "nation_name": n.nation_name} for n in items
    ]}}


@router.get("/regions/gu", summary="서울 자치구 목록 (25개)")
def get_gu_list(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT gu_id, gu_name FROM sigungu ORDER BY gu_name")).fetchall()
    return {"success": True, "data": {"gus": [
        {"gu_id": r[0], "gu_name": r[1]} for r in rows
    ]}}
