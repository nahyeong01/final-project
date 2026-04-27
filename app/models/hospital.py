# ====================================================
#  models/hospital.py — 병원 관련 테이블 ORM 모델
# ====================================================

from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Numeric, ForeignKey, DateTime
from app.db import Base


class MedicalDept(Base):
    """진료과 테이블"""
    __tablename__ = "medical_dept"

    medi_dept_id   = Column(String(36),  primary_key=True)
    medi_dept_name = Column(String(100), nullable=False)


class MedicalProcedure(Base):
    """시술 정보 테이블 — 챗봇 RAG 소스"""
    __tablename__ = "medical_procedure"

    proc_id      = Column(String(36),  primary_key=True)
    medi_dept_id = Column(String(36),  ForeignKey("medical_dept.medi_dept_id"))
    proc_name    = Column(String(100), nullable=False)
    proc_desc    = Column(Text)
    before_caut  = Column(Text)
    after_note   = Column(Text)
    after_caut   = Column(Text)
    side_eff     = Column(Text)
    hosp_req_sym = Column(Text)
    created_at   = Column(DateTime, default=datetime.utcnow)


class Hospital(Base):
    """병원 정보 테이블"""
    __tablename__ = "hospital"

    hosp_id       = Column(String(36),  primary_key=True)
    dong_id       = Column(String(8))
    hosp_name     = Column(String(200), nullable=False)
    addr          = Column(String(300))
    lat           = Column(Numeric(30, 25))
    lon           = Column(Numeric(30, 25))
    hosp_url      = Column(String(500))
    kahf          = Column(String(1))
    coordinator   = Column(String(1))
    online_reserv = Column(String(1))
    facility_info = Column(Text)
    history       = Column(Text)
    sns_url       = Column(String(500))
    created_at    = Column(DateTime, default=datetime.utcnow)


class HospitalDept(Base):
    """병원-진료과 매핑 테이블"""
    __tablename__ = "hospital_dept"

    hosp_dept_id = Column(String(36), primary_key=True)
    hosp_id      = Column(String(36), ForeignKey("hospital.hosp_id"))
    medi_dept_id = Column(String(36), ForeignKey("medical_dept.medi_dept_id"))


class HospitalProcedure(Base):
    """병원-시술 매핑 테이블"""
    __tablename__ = "hospital_procedure"

    hosp_proc_id = Column(String(36), primary_key=True)
    proc_id      = Column(String(36), ForeignKey("medical_procedure.proc_id"))
    hosp_dept_id = Column(String(36), ForeignKey("hospital_dept.hosp_dept_id"))


class ServiceLang(Base):
    """외국어 서비스 언어 코드 테이블"""
    __tablename__ = "service_lang"

    svc_lang_id   = Column(String(36), primary_key=True)
    svc_lang_name = Column(String(50), nullable=False)


class HospitalServiceLang(Base):
    """병원-외국어서비스 매핑 테이블"""
    __tablename__ = "hospital_service_lang"

    hosp_svc_lang_id = Column(String(36), primary_key=True)
    hosp_id          = Column(String(36), ForeignKey("hospital.hosp_id"))
    svc_lang_id      = Column(String(36), ForeignKey("service_lang.svc_lang_id"))


class AfterCautionTag(Base):
    """시술 후 주의사항 태그 테이블"""
    __tablename__ = "after_caution_tag"

    after_caut_tag_id = Column(String(36),  primary_key=True)
    after_caut_tag    = Column(String(100), nullable=False)
    created_at        = Column(DateTime, default=datetime.utcnow)


class ProcCautionMap(Base):
    """시술-주의사항 태그 매핑 테이블"""
    __tablename__ = "proc_caution_map"

    proc_caut_map_id  = Column(String(36), primary_key=True)
    proc_id           = Column(String(36), ForeignKey("medical_procedure.proc_id"))
    after_caut_tag_id = Column(String(36), ForeignKey("after_caution_tag.after_caut_tag_id"))


class HospitalWishlist(Base):
    """병원 찜 목록"""
    __tablename__ = "hospital_wishlist"

    hosp_wish_id = Column(String(36), primary_key=True)
    user_id      = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    hosp_id      = Column(String(36), ForeignKey("hospital.hosp_id"), nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)
