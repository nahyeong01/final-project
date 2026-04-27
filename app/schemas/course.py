# ====================================================
#  schemas/course.py — 코스 & 여행일정 관련 요청/응답 스키마
# ====================================================

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


# ── 여행 일정 ──────────────────────────────────────

class TripCreateRequest(BaseModel):
    """여행 일정 생성 요청"""
    trip_start: date
    trip_end:   date


class TripProcedureRequest(BaseModel):
    """시술/병원 확정 저장 요청. 건너뛰기 시 hosp_proc_id = null"""
    hosp_proc_id: Optional[str] = None


# ── 코스 ───────────────────────────────────────────

class CourseSpot(BaseModel):
    """코스 내 관광지 아이템"""
    tour_id:     str
    tour_name:   str
    visit_order: int
    addr:        Optional[str]
    img_url:     Optional[str]
    lat:         Optional[float]
    lon:         Optional[float]


class CourseDay(BaseModel):
    """일차별 코스"""
    day:   int
    date:  Optional[date]
    spots: List[CourseSpot] = []


class CourseDetailItem(BaseModel):
    """코스 저장 시 detail 항목 하나"""
    tour_id:     str
    day:         int
    visit_order: int


class CourseSaveRequest(BaseModel):
    """코스 저장 요청"""
    course_name: str
    course_type: str   # "AI" 또는 "CUSTOM"
    trip_id:     str
    details:     List[CourseDetailItem]


class CourseUpdateRequest(BaseModel):
    """코스 수정 요청 (DnD 순서 변경 후 전체 재전송)"""
    course_name: Optional[str] = None
    details:     List[CourseDetailItem]


class CourseCard(BaseModel):
    """코스 목록 카드 응답"""
    course_id:   str
    course_name: str
    course_type: str
    trip_start:  Optional[date]
    trip_end:    Optional[date]
    proc_names:  List[str] = []
    spot_count:  int = 0
    created_at:  Optional[datetime]


class CourseDetailResponse(BaseModel):
    """코스 상세 응답"""
    course_id:   str
    course_name: str
    course_type: str
    trip_start:  Optional[date]
    trip_end:    Optional[date]
    days:        List[CourseDay] = []
