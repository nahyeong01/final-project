# ====================================================
#  schemas/chatbot.py — AI 챗봇 관련 요청/응답 스키마
# ====================================================

from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    """챗봇 메시지 요청"""
    message:    str
    session_id: Optional[str] = None   # 대화 세션 유지용
    language:   str = "en"             # ko | en | zh | ja | th


class ChatResponse(BaseModel):
    """챗봇 응답"""
    reply:        str
    session_id:   Optional[str]
    caution_tags: List[str] = []   # 위험 경고 UI 트리거용
    references:   List[dict] = []  # 참조 시술 DB 항목


class ImageAnalysisResponse(BaseModel):
    """얼굴 이미지 분석 응답"""
    analysis_text: str
    risk_level:    str   # "normal" | "caution" | "danger"
    session_id:    Optional[str]
