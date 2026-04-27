# ====================================================
#  schemas/hospital.py — 병원 & 시술 관련 요청/응답 스키마
# ====================================================

from pydantic import BaseModel
from typing import Optional, List


class HospitalCard(BaseModel):
    """병원 목록 카드 응답"""
    hosp_id:        str
    hosp_name:      str
    addr:           Optional[str]
    lat:            Optional[float]
    lon:            Optional[float]
    kahf:           Optional[int]
    coordinator:    Optional[int]
    medi_dept_names: List[str] = []
    proc_names:      List[str] = []
    svc_lang_names:  List[str] = []
    distance_km:    Optional[float] = None


class HospitalDetail(BaseModel):
    """병원 상세 응답"""
    hosp_id:       str
    hosp_name:     str
    addr:          Optional[str]
    lat:           Optional[float]
    lon:           Optional[float]
    hosp_url:      Optional[str]
    kahf:          Optional[int]
    coordinator:   Optional[int]
    online_reserv: Optional[int]
    facility_info: Optional[str]
    history:       Optional[str]
    sns_url:       Optional[str]
    medi_depts:    List[dict] = []
    procedures:    List[dict] = []
    service_langs: List[dict] = []


class ProcedureItem(BaseModel):
    """시술 목록 아이템"""
    proc_id:       str
    proc_name:     str
    medi_dept_id:  Optional[str]
    medi_dept_name: Optional[str]


class ProcedureDetail(BaseModel):
    """시술 상세 응답"""
    proc_id:      str
    proc_name:    str
    proc_desc:    Optional[str]
    before_caut:  Optional[str]
    after_note:   Optional[str]
    after_caut:   Optional[str]
    side_eff:     Optional[str]
    hosp_req_sym: Optional[str]


class WishlistToggleResponse(BaseModel):
    """찜 추가/해제 응답"""
    hosp_wish_id: Optional[str]
    message:      Optional[str]
