# ====================================================
#  services/llm.py — LLM 연동 서비스
#  챗봇 RAG 응답, 긴급문자 자동 생성, 얼굴 이미지 분석
# ====================================================

import base64
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

# 언어 코드 → 언어명 변환
LANGUAGE_MAP = {
    "ko": "한국어",
    "en": "영어",
    "zh": "중국어",
    "ja": "일본어",
    "th": "태국어",
}


def chat_with_rag(
    db:         Session,
    message:    str,
    language:   str = "en",
    session_id: str = None,
) -> dict:
    """
    시술 정보 DB 기반 RAG 챗봇 응답

    1. 메시지에서 시술 관련 키워드 추출
    2. Oracle DB에서 해당 시술 정보 조회
    3. DB 내용을 컨텍스트로 LLM에 전달
    """
    lang_name = LANGUAGE_MAP.get(language, "영어")

    # ── DB에서 시술 정보 검색 ─────────────────────
    proc_sql = text("""
        SELECT proc_name, proc_desc, before_caut, after_note,
               after_caut, side_eff, hosp_req_sym
        FROM medical_procedure
        WHERE LOWER(proc_name) LIKE LOWER(:keyword)
           OR LOWER(proc_desc) LIKE LOWER(:keyword)
        FETCH FIRST 3 ROWS ONLY
    """)
    # 메시지 전체를 키워드로 사용 (간단한 방식, 추후 NLP 고도화 가능)
    keyword = f"%{message[:20]}%"
    procs = db.execute(proc_sql, {"keyword": keyword}).fetchall()

    proc_context = ""
    references = []
    if procs:
        for p in procs:
            r = dict(p._mapping)
            references.append({"proc_name": r.get("proc_name")})
            proc_context += f"""
시술명: {r.get('proc_name')}
설명: {r.get('proc_desc', '')}
시술 전 주의: {r.get('before_caut', '')}
시술 후 안내: {r.get('after_note', '')}
시술 후 주의: {r.get('after_caut', '')}
부작용: {r.get('side_eff', '')}
병원 방문 필요 증상: {r.get('hosp_req_sym', '')}
---"""

    system_prompt = f"""너는 한국 의료관광 전문 AI 어시스턴트야.
아래 의료 데이터베이스 정보를 참고해서 {lang_name}로 답변해줘.
정확하지 않은 의료 정보는 제공하지 말고, 모르면 병원 상담을 권유해줘.

[의료 DB 정보]
{proc_context if proc_context else "관련 시술 정보 없음"}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": message},
        ],
        max_tokens=800,
    )

    reply = response.choices[0].message.content

    # 위험 경고 키워드 체크 (간단한 규칙 기반)
    caution_tags = []
    danger_keywords = ["즉시", "응급", "병원 방문", "위험", "emergency", "immediately"]
    if any(kw in reply for kw in danger_keywords):
        caution_tags.append("의료진 상담 권장")

    return {
        "reply":        reply,
        "session_id":   session_id,
        "caution_tags": caution_tags,
        "references":   references,
    }


def analyze_face_image(image_bytes: bytes, session_id: str = None) -> dict:
    """
    얼굴 이미지 분석 → 피부 상태 + 위험 단계 반환
    OpenAI Vision API 사용
    """
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "이 얼굴 이미지의 피부 상태를 분석해줘. "
                            "다음 형식으로 답해줘:\n"
                            "1. 피부 상태 설명 (2-3문장)\n"
                            "2. 위험 단계: normal(정상) / caution(주의) / danger(위험) 중 하나만\n"
                            "의료적 진단이 아닌 일반적인 피부 상태 설명임을 명시해줘."
                        ),
                    },
                    {
                        "type":      "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
        max_tokens=500,
    )

    analysis_text = response.choices[0].message.content

    # 위험 단계 파싱
    risk_level = "normal"
    if "danger" in analysis_text.lower() or "위험" in analysis_text:
        risk_level = "danger"
    elif "caution" in analysis_text.lower() or "주의" in analysis_text:
        risk_level = "caution"

    return {
        "analysis_text": analysis_text,
        "risk_level":    risk_level,
        "session_id":    session_id,
    }


def generate_emergency_message(
    db:                Session,
    input_language:    str,
    symptom_text:      str,
    user_hosp_proc_id: str = None,
) -> str:
    """
    긴급문자 자동 생성
    시술명 + 병원명 + 증상을 조합해서 지정 언어로 번역된 긴급문자 생성
    """
    lang_name = LANGUAGE_MAP.get(input_language, input_language)

    proc_name = ""
    hosp_name = ""

    # 시술-병원 정보 조회
    if user_hosp_proc_id:
        info_sql = text("""
            SELECT mp.proc_name, h.hosp_name
            FROM user_hospital_procedure uhp
            JOIN hospital_procedure hp ON uhp.hosp_proc_id = hp.hosp_proc_id
            JOIN medical_procedure mp   ON hp.proc_id = mp.proc_id
            JOIN hospital h             ON hp.hosp_id = h.hosp_id
            WHERE uhp.user_hosp_proc_id = :id
        """)
        info = db.execute(info_sql, {"id": user_hosp_proc_id}).fetchone()
        if info:
            proc_name = info[0] or ""
            hosp_name = info[1] or ""

    proc_line = f"- 시술: {proc_name} ({hosp_name})" if proc_name else ""

    prompt = f"""아래 정보를 바탕으로 {lang_name}로 응급 구조대원이 즉시 이해할 수 있는 긴급문자를 작성해줘.
짧고 명확하게, 핵심 정보만 포함해줘.

{proc_line}
- 증상: {symptom_text}

[출력 형식]
제목: 응급 상황 / Emergency
내용: (100자 이내)"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )

    return response.choices[0].message.content
