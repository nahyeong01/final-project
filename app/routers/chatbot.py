# ====================================================
#  routers/chatbot.py — AI 챗봇 API
#  POST /api/chatbot/message        챗봇 메시지 (RAG 응답)
#  POST /api/chatbot/analyze-image  얼굴 이미지 분석 (Vision API)
# ====================================================

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.dependencies import get_current_user
from app.schemas.chatbot import ChatRequest
from app.services.llm import chat_with_rag, analyze_face_image

router = APIRouter()


@router.post("/message", summary="챗봇 메시지 전송 (RAG 응답)")
def chatbot_message(
    req:     ChatRequest,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),
):
    """
    시술 정보 DB 기반 RAG 방식으로 질문에 답변
    - DB에서 관련 시술 정보 조회 → LLM 컨텍스트로 전달
    - caution_tags: 위험 경고 시 UI 배너 표시용
    - references: 참조한 시술 DB 항목 목록
    """
    result = chat_with_rag(
        db=db,
        message=req.message,
        language=req.language,
        session_id=req.session_id,
    )
    return {"success": True, "data": result}


@router.post("/analyze-image", summary="얼굴 이미지 분석 (Vision API)")
async def analyze_image(
    session_id: Optional[str] = Form(None),
    image:      UploadFile     = File(..., description="얼굴 이미지 파일"),
    db:         Session        = Depends(get_db),
    user_id:    str            = Depends(get_current_user),
):
    """
    얼굴 사진 업로드 → OpenAI Vision API로 피부 상태 분석
    - analysis_text: 피부 상태 설명
    - risk_level: normal(정상) / caution(주의) / danger(위험)
    """
    # 이미지 파일 크기 제한 (10MB)
    MAX_SIZE = 10 * 1024 * 1024
    image_bytes = await image.read()
    if len(image_bytes) > MAX_SIZE:
        raise HTTPException(400, detail="이미지 파일 크기가 10MB를 초과합니다.")

    # 이미지 형식 확인
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if image.content_type not in allowed_types:
        raise HTTPException(400, detail="JPEG, PNG, WEBP 형식의 이미지만 업로드 가능합니다.")

    result = analyze_face_image(image_bytes=image_bytes, session_id=session_id)
    return {"success": True, "data": result}
