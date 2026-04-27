# ====================================================
#  routers/users.py — 사용자 API
# ====================================================

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User, Nationality
from app.models.emergency import (
    Allergy, Medication, UserDisease, EmergencyContact
)
from app.schemas.emergency import (
    AllergyCreate, MedicationCreate, DiseaseCreate, EmergencyContactCreate
)

router = APIRouter()


# ── 프로필 ────────────────────────────────────────

@router.get("/me", summary="내 프로필 조회")
def get_my_profile(
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(404, detail="사용자를 찾을 수 없습니다.")

    nation = db.query(Nationality).filter(Nationality.nation_id == user.nation_id).first()

    return {
        "success": True,
        "data": {
            "user_id":    user.user_id,
            "first_name": user.first_name,
            "last_name":  user.last_name,
            "email":      user.email,
            "tel":        user.tel,
            "blood_type": user.blood_type,
            "sex":        user.sex,
            "nation_id":  user.nation_id,
            "nation_name": nation.nation_name if nation else None,
        }
    }


@router.put("/me", summary="내 프로필 수정")
def update_my_profile(
    first_name: Optional[str] = None,
    last_name:  Optional[str] = None,
    tel:        Optional[str] = None,
    blood_type: Optional[str] = None,
    sex:        Optional[str] = None,
    nation_id:  Optional[str] = None,
    db:         Session = Depends(get_db),
    user_id:    str     = Depends(get_current_user),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(404, detail="사용자를 찾을 수 없습니다.")

    if first_name: user.first_name = first_name
    if last_name:  user.last_name  = last_name
    if tel:        user.tel        = tel
    if blood_type: user.blood_type = blood_type
    if sex:        user.sex        = sex
    if nation_id:  user.nation_id  = nation_id

    db.commit()
    db.refresh(user)
    return {"success": True, "data": {
        "user_id":    user.user_id,
        "first_name": user.first_name,
        "last_name":  user.last_name,
    }}


@router.get("/me/medical-info", summary="긴급 의료정보 통합 조회")
def get_medical_info(
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    user      = db.query(User).filter(User.user_id == user_id).first()
    allergies = db.query(Allergy).filter(Allergy.user_id == user_id).all()
    meds      = db.query(Medication).filter(Medication.user_id == user_id).all()
    diseases  = db.query(UserDisease).filter(UserDisease.user_id == user_id).all()
    contacts  = db.query(EmergencyContact).filter(EmergencyContact.user_id == user_id).all()

    return {
        "success": True,
        "data": {
            "blood_type": user.blood_type if user else None,
            "allergies":  [{"alrg_id": a.alrg_id, "alrg_name": a.alrg_name} for a in allergies],
            "medications": [{"med_id": m.med_id, "med_name": m.med_name, "dsg": m.dsg, "freq": m.freq} for m in meds],
            "diseases":   [{"user_dis_id": d.user_dis_id, "user_dis_name": d.user_dis_name} for d in diseases],
            "emergency_contacts": [
                {"emrg_contact_id": c.emrg_contact_id, "contact_name": c.contact_name,
                 "relationship": c.relationship, "tel": c.tel}
                for c in contacts
            ],
        }
    }


# ── 알레르기 ──────────────────────────────────────

@router.get("/me/allergies", summary="알레르기 목록")
def get_allergies(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    items = db.query(Allergy).filter(Allergy.user_id == user_id).all()
    return {"success": True, "data": {"allergies": [{"alrg_id": i.alrg_id, "alrg_name": i.alrg_name} for i in items]}}


@router.post("/me/allergies", status_code=201, summary="알레르기 추가")
def add_allergy(req: AllergyCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    item = Allergy(alrg_id=str(uuid.uuid4()), user_id=user_id, alrg_name=req.alrg_name)
    db.add(item)
    db.commit()
    return {"success": True, "data": {"alrg_id": item.alrg_id}}


@router.delete("/me/allergies/{alrg_id}", summary="알레르기 삭제")
def delete_allergy(alrg_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    item = db.query(Allergy).filter(Allergy.alrg_id == alrg_id, Allergy.user_id == user_id).first()
    if not item:
        raise HTTPException(404, detail="항목을 찾을 수 없습니다.")
    db.delete(item)
    db.commit()
    return {"success": True, "data": {"message": "Deleted"}}


# ── 복용약 ───────────────────────────────────────

@router.get("/me/medications", summary="복용약 목록")
def get_medications(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    items = db.query(Medication).filter(Medication.user_id == user_id).all()
    return {"success": True, "data": {"medications": [
        {"med_id": i.med_id, "med_name": i.med_name, "dsg": i.dsg, "freq": i.freq} for i in items
    ]}}


@router.post("/me/medications", status_code=201, summary="복용약 추가")
def add_medication(req: MedicationCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    item = Medication(med_id=str(uuid.uuid4()), user_id=user_id,
                      med_name=req.med_name, dsg=req.dsg, freq=req.freq)
    db.add(item)
    db.commit()
    return {"success": True, "data": {"med_id": item.med_id}}


@router.delete("/me/medications/{med_id}", summary="복용약 삭제")
def delete_medication(med_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    item = db.query(Medication).filter(Medication.med_id == med_id, Medication.user_id == user_id).first()
    if not item:
        raise HTTPException(404, detail="항목을 찾을 수 없습니다.")
    db.delete(item)
    db.commit()
    return {"success": True, "data": {"message": "Deleted"}}


# ── 기저질환 ──────────────────────────────────────

@router.get("/me/diseases", summary="기저질환 목록")
def get_diseases(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    items = db.query(UserDisease).filter(UserDisease.user_id == user_id).all()
    return {"success": True, "data": {"diseases": [
        {"user_dis_id": i.user_dis_id, "user_dis_name": i.user_dis_name} for i in items
    ]}}


@router.post("/me/diseases", status_code=201, summary="기저질환 추가")
def add_disease(req: DiseaseCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    item = UserDisease(user_dis_id=str(uuid.uuid4()), user_id=user_id, user_dis_name=req.user_dis_name)
    db.add(item)
    db.commit()
    return {"success": True, "data": {"user_dis_id": item.user_dis_id}}


@router.delete("/me/diseases/{user_dis_id}", summary="기저질환 삭제")
def delete_disease(user_dis_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    item = db.query(UserDisease).filter(UserDisease.user_dis_id == user_dis_id, UserDisease.user_id == user_id).first()
    if not item:
        raise HTTPException(404, detail="항목을 찾을 수 없습니다.")
    db.delete(item)
    db.commit()
    return {"success": True, "data": {"message": "Deleted"}}


# ── 비상연락처 ─────────────────────────────────────

@router.get("/me/emergency-contacts", summary="비상연락처 목록")
def get_emergency_contacts(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    items = db.query(EmergencyContact).filter(EmergencyContact.user_id == user_id).all()
    return {"success": True, "data": {"contacts": [
        {"emrg_contact_id": i.emrg_contact_id, "contact_name": i.contact_name,
         "relationship": i.relationship, "tel": i.tel}
        for i in items
    ]}}


@router.post("/me/emergency-contacts", status_code=201, summary="비상연락처 추가")
def add_emergency_contact(req: EmergencyContactCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    item = EmergencyContact(
        emrg_contact_id=str(uuid.uuid4()), user_id=user_id,
        contact_name=req.contact_name, relationship=req.relationship, tel=req.tel
    )
    db.add(item)
    db.commit()
    return {"success": True, "data": {"emrg_contact_id": item.emrg_contact_id}}


@router.delete("/me/emergency-contacts/{emrg_contact_id}", summary="비상연락처 삭제")
def delete_emergency_contact(emrg_contact_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    item = db.query(EmergencyContact).filter(
        EmergencyContact.emrg_contact_id == emrg_contact_id,
        EmergencyContact.user_id == user_id
    ).first()
    if not item:
        raise HTTPException(404, detail="항목을 찾을 수 없습니다.")
    db.delete(item)
    db.commit()
    return {"success": True, "data": {"message": "Deleted"}}
