# ====================================================
#  routers/emergency.py — 긴급대응키트 API
#  GET  /api/emergency/rooms            주변 응급실 목록
#  POST /api/emergency/records          긴급 기록 저장
#  POST /api/emergency/message/generate 긴급문자 자동 생성
#  GET  /api/location/address           좌표 → 주소 변환 (카카오)
# ====================================================

import uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.emergency import EmergencyRoom, EmergencyRecord
from app.schemas.emergency import EmergencyRecordCreate, EmergencyMsgRequest
from app.services.haversine import haversine
from app.services.llm import generate_emergency_message
from app.config import KAKAO_REST_API_KEY

router = APIRouter()


# ── 주변 응급실 목록 ──────────────────────────────

@router.get("/rooms", summary="주변 응급실 목록 (GPS 반경 조회)")
def get_emergency_rooms(
    lat:       float = Query(..., description="현재 위도"),
    lon:       float = Query(..., description="현재 경도"),
    radius_km: float = Query(5.0, description="검색 반경 km"),
    db:        Session = Depends(get_db),
    user_id:   str     = Depends(get_current_user),
):
    rooms  = db.query(EmergencyRoom).all()
    result = []

    for room in rooms:
        if not room.lat or not room.lon:
            continue
        dist = haversine(lat, lon, float(room.lat), float(room.lon))
        if dist <= radius_km:
            result.append({
                "emrg_room_id":   room.emrg_room_id,
                "emrg_room_name": room.emrg_room_name,
                "lat":            float(room.lat),
                "lon":            float(room.lon),
                "tel":            room.tel,
                "note":           room.note,
                "distance_km":    dist,
            })

    result.sort(key=lambda x: x["distance_km"])
    return {"success": True, "data": {"rooms": result}}


# ── 긴급 기록 저장 ────────────────────────────────

@router.post("/records", status_code=201, summary="긴급 기록 저장")
def save_emergency_record(
    req:     EmergencyRecordCreate,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    record = EmergencyRecord(
        emrg_record_id = str(uuid.uuid4()),
        user_id        = user_id,
        emrg_room_id   = req.emrg_room_id,
        lat            = req.lat,
        lon            = req.lon,
        addr           = req.addr,
        addr_src       = req.addr_src,
        msg_txt        = req.msg_txt,
    )
    db.add(record)
    db.commit()
    return {"success": True, "data": {"emrg_record_id": record.emrg_record_id}}


# ── 긴급문자 자동 생성 (LLM) ─────────────────────

@router.post("/message/generate", summary="긴급문자 LLM 자동 생성")
def generate_msg(
    req:     EmergencyMsgRequest,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    """
    시술명 + 병원명 + 증상 → LLM이 지정 언어로 긴급문자 자동 생성
    """
    msg = generate_emergency_message(
        db=db,
        input_language=req.input_language,
        symptom_text=req.symptom_text,
        user_hosp_proc_id=req.user_hosp_proc_id,
    )
    return {"success": True, "data": {"generated_message": msg}}


# ── 좌표 → 주소 변환 (카카오 Reverse Geocoding) ───

@router.get("/location/address", summary="좌표 → 주소 변환")
async def get_address(
    lat:     float = Query(..., description="위도"),
    lon:     float = Query(..., description="경도"),
    user_id: str   = Depends(get_current_user),
):
    """
    ⚠️ 카카오 파라미터 주의: x = 경도(lon), y = 위도(lat) 순서!
    일반적인 lat/lon 순서와 반대임
    """
    url     = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params  = {"x": lon, "y": lat}   # x = 경도, y = 위도

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        data = resp.json()

    if not data.get("documents"):
        raise HTTPException(404, detail="주소를 찾을 수 없습니다.")

    addr_info = data["documents"][0]["address"]
    return {
        "success": True,
        "data": {
            "address":   addr_info.get("address_name"),
            "gu_name":   addr_info.get("region_2depth_name"),
            "dong_name": addr_info.get("region_3depth_name"),
        }
    }
