# ====================================================
#  routers/courses.py — 코스 & 여행일정 API
#  POST /api/trips                      여행 일정 생성
#  POST /api/trips/{trip_id}/procedure  시술/병원 확정 저장
#  GET  /api/courses/recommend          AI 자동 추천 코스
#  POST /api/courses                    코스 저장
#  GET  /api/courses                    저장된 코스 목록
#  GET  /api/courses/{course_id}        코스 상세
#  PUT  /api/courses/{course_id}        코스 수정 (DnD)
#  DELETE /api/courses/{course_id}      코스 삭제
#  GET  /api/courses/{course_id}/export 코스 PDF 내보내기
# ====================================================

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional
import io

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import UserTrip, UserHospitalProcedure
from app.models.course import Course, CourseDetail
from app.schemas.course import (
    TripCreateRequest, TripProcedureRequest,
    CourseSaveRequest, CourseUpdateRequest,
)
from app.services.recommend import recommend_course

router = APIRouter()


# ── 여행 일정 ─────────────────────────────────────

@router.post("/trips", status_code=201, summary="여행 일정 생성")
def create_trip(
    req:     TripCreateRequest,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    trip = UserTrip(
        trip_id    = str(uuid.uuid4()),
        user_id    = user_id,
        trip_start = req.trip_start,
        trip_end   = req.trip_end,
    )
    db.add(trip)
    db.commit()
    return {"success": True, "data": {"trip_id": trip.trip_id, "trip_start": str(req.trip_start), "trip_end": str(req.trip_end)}}


@router.post("/trips/{trip_id}/procedure", status_code=201, summary="시술/병원 확정 저장")
def save_trip_procedure(
    trip_id: str,
    req:     TripProcedureRequest,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    """
    병원 건너뛰기 시 hosp_proc_id = null로 저장
    """
    uhp = UserHospitalProcedure(
        user_hosp_proc_id = str(uuid.uuid4()),
        user_id           = user_id,
        trip_id           = trip_id,
        hosp_proc_id      = req.hosp_proc_id,   # None 허용
    )
    db.add(uhp)
    db.commit()
    return {"success": True, "data": {"user_hosp_proc_id": uhp.user_hosp_proc_id}}


# ── AI 자동 추천 코스 ─────────────────────────────

@router.get("/courses/recommend", summary="AI 자동 추천 코스 생성")
def get_recommended_course(
    trip_id:  str           = Query(..., description="여행 일정 ID"),
    proc_id:  Optional[str] = Query(None, description="시술 ID"),
    acc_lat:  Optional[float] = Query(None, description="숙소 위도"),
    acc_lon:  Optional[float] = Query(None, description="숙소 경도"),
    seed:     Optional[int]   = Query(None, description="새로고침용 랜덤 시드"),
    db:       Session         = Depends(get_db),
    user_id:  str             = Depends(get_current_user),
):
    # 사용자 국적 조회
    user_row = db.execute(
        text("SELECT nation_id FROM users WHERE user_id = :uid"),
        {"uid": user_id}
    ).fetchone()
    nation_id = user_row[0] if user_row else None

    days = recommend_course(
        db=db, user_id=user_id, trip_id=trip_id,
        proc_id=proc_id, nation_id=nation_id,
        acc_lat=acc_lat, acc_lon=acc_lon, seed=seed,
    )
    return {"success": True, "data": {"days": days}}


# ── 코스 저장 / 목록 ──────────────────────────────

@router.post("/courses", status_code=201, summary="코스 저장")
def save_course(
    req:     CourseSaveRequest,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    course = Course(
        course_id   = str(uuid.uuid4()),
        user_id     = user_id,
        trip_id     = req.trip_id,
        course_name = req.course_name,
        course_type = req.course_type,
    )
    db.add(course)

    for d in req.details:
        detail = CourseDetail(
            course_detail_id = str(uuid.uuid4()),
            course_id        = course.course_id,
            tour_id          = d.tour_id,
            day              = d.day,
            visit_order      = d.visit_order,
        )
        db.add(detail)

    db.commit()
    return {"success": True, "data": {"course_id": course.course_id}}


@router.get("/courses", summary="저장된 코스 목록")
def get_courses(
    course_type: Optional[str] = Query(None, description="AI | CUSTOM | 전체"),
    db:          Session       = Depends(get_db),
    user_id:     str           = Depends(get_current_user),
):
    query = db.query(Course).filter(Course.user_id == user_id)
    if course_type:
        query = query.filter(Course.course_type == course_type)

    courses = query.order_by(Course.created_at.desc()).all()
    result  = []

    for c in courses:
        trip = db.query(UserTrip).filter(UserTrip.trip_id == c.trip_id).first()
        spot_count = db.query(CourseDetail).filter(CourseDetail.course_id == c.course_id).count()

        result.append({
            "course_id":   c.course_id,
            "course_name": c.course_name,
            "course_type": c.course_type,
            "trip_start":  str(trip.trip_start) if trip else None,
            "trip_end":    str(trip.trip_end) if trip else None,
            "spot_count":  spot_count,
            "created_at":  str(c.created_at),
        })

    return {"success": True, "data": {"courses": result}}


# ── 코스 상세 / 수정 / 삭제 ──────────────────────

@router.get("/courses/{course_id}", summary="코스 상세")
def get_course_detail(
    course_id: str,
    db:        Session = Depends(get_db),
    user_id:   str     = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.course_id == course_id, Course.user_id == user_id).first()
    if not course:
        raise HTTPException(404, detail="코스를 찾을 수 없습니다.")

    trip    = db.query(UserTrip).filter(UserTrip.trip_id == course.trip_id).first()
    details = db.query(CourseDetail).filter(CourseDetail.course_id == course_id).order_by(
        CourseDetail.day, CourseDetail.visit_order
    ).all()

    # 일차별 그룹핑
    from datetime import timedelta
    days_map = {}
    for d in details:
        if d.day not in days_map:
            days_map[d.day] = []

        spot_row = db.execute(
            text("SELECT tour_name, addr, img_url, lat, lon FROM tourist WHERE tour_id = :id"),
            {"id": d.tour_id}
        ).fetchone()

        if spot_row:
            days_map[d.day].append({
                "tour_id":     d.tour_id,
                "tour_name":   spot_row[0],
                "visit_order": d.visit_order,
                "addr":        spot_row[1],
                "img_url":     spot_row[2],
                "lat":         float(spot_row[3]) if spot_row[3] else None,
                "lon":         float(spot_row[4]) if spot_row[4] else None,
            })

    trip_start = trip.trip_start if trip else None
    days_list  = []
    for day_num, spots in sorted(days_map.items()):
        day_date = None
        if trip_start:
            from datetime import timedelta
            day_date = str((trip_start + timedelta(days=day_num - 1)).date())
        days_list.append({"day": day_num, "date": day_date, "spots": spots})

    return {
        "success": True,
        "data": {
            "course_id":   course.course_id,
            "course_name": course.course_name,
            "course_type": course.course_type,
            "trip_start":  str(trip.trip_start) if trip else None,
            "trip_end":    str(trip.trip_end) if trip else None,
            "days":        days_list,
        }
    }


@router.put("/courses/{course_id}", summary="코스 수정 (DnD 저장)")
def update_course(
    course_id: str,
    req:       CourseUpdateRequest,
    db:        Session = Depends(get_db),
    user_id:   str     = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.course_id == course_id, Course.user_id == user_id).first()
    if not course:
        raise HTTPException(404, detail="코스를 찾을 수 없습니다.")

    if req.course_name:
        course.course_name = req.course_name

    # 기존 course_detail 전체 삭제 후 재삽입
    db.query(CourseDetail).filter(CourseDetail.course_id == course_id).delete()
    for d in req.details:
        db.add(CourseDetail(
            course_detail_id=str(uuid.uuid4()),
            course_id=course_id,
            tour_id=d.tour_id,
            day=d.day,
            visit_order=d.visit_order,
        ))

    db.commit()
    return {"success": True, "data": {"course_id": course_id}}


@router.delete("/courses/{course_id}", summary="코스 삭제")
def delete_course(
    course_id: str,
    db:        Session = Depends(get_db),
    user_id:   str     = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.course_id == course_id, Course.user_id == user_id).first()
    if not course:
        raise HTTPException(404, detail="코스를 찾을 수 없습니다.")

    db.query(CourseDetail).filter(CourseDetail.course_id == course_id).delete()
    db.delete(course)
    db.commit()
    return {"success": True, "data": {"message": "Deleted"}}


# ── PDF 내보내기 ───────────────────────────────────

@router.get("/courses/{course_id}/export", summary="코스 PDF 내보내기")
def export_course_pdf(
    course_id: str,
    db:        Session = Depends(get_db),
    user_id:   str     = Depends(get_current_user),
):
    """
    코스 일정을 PDF로 생성하여 다운로드
    ReportLab 라이브러리 사용
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.lib.units import cm

    course = db.query(Course).filter(Course.course_id == course_id, Course.user_id == user_id).first()
    if not course:
        raise HTTPException(404, detail="코스를 찾을 수 없습니다.")

    details = db.query(CourseDetail).filter(CourseDetail.course_id == course_id).order_by(
        CourseDetail.day, CourseDetail.visit_order
    ).all()

    # PDF 생성
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, height - 3 * cm, f"K-MEDITRIP Course: {course.course_name}")

    y = height - 5 * cm
    c.setFont("Helvetica", 11)

    current_day = 0
    for d in details:
        if d.day != current_day:
            current_day = d.day
            y -= 0.5 * cm
            c.setFont("Helvetica-Bold", 12)
            c.drawString(2 * cm, y, f"Day {current_day}")
            y -= 0.5 * cm
            c.setFont("Helvetica", 10)

        spot_row = db.execute(
            text("SELECT tour_name, addr FROM tourist WHERE tour_id = :id"),
            {"id": d.tour_id}
        ).fetchone()

        if spot_row:
            c.drawString(3 * cm, y, f"{d.visit_order}. {spot_row[0]}  |  {spot_row[1] or ''}")
            y -= 0.5 * cm

        if y < 3 * cm:
            c.showPage()
            y = height - 3 * cm

    c.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=kmeditrip_{course_id}.pdf"}
    )
