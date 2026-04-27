# ====================================================
#  schemas/emergency.py — 긴급대응키트 관련 요청/응답 스키마
# ====================================================

from pydantic import BaseModel
from typing import Optional


class AllergyCreate(BaseModel):
    alrg_name: str

class MedicationCreate(BaseModel):
    med_name: str
    dsg:      Optional[str] = None   # 용량
    freq:     Optional[str] = None   # 복용 빈도

class DiseaseCreate(BaseModel):
    user_dis_name: str

class EmergencyContactCreate(BaseModel):
    contact_name: str
    relationship: Optional[str] = None
    tel:          str


class EmergencyRecordCreate(BaseModel):
    """긴급 기록 저장 요청"""
    emrg_room_id: Optional[str] = None
    lat:          float
    lon:          float
    addr:         Optional[str] = None
    addr_src:     Optional[str] = "kakao"
    msg_txt:      Optional[str] = None


class EmergencyMsgRequest(BaseModel):
    """긴급문자 자동생성 요청"""
    input_language:    str   # 영어 | 중국어 | 일본어 | 태국어 | 한국어
    symptom_text:      str   # 증상 입력
    user_hosp_proc_id: Optional[str] = None   # 없으면 시술/병원 정보 미포함
