# ====================================================
#  main.py — FastAPI 앱 진입점
#  서버를 켜면 가장 먼저 실행되는 파일
#  실행 명령어: uvicorn app.main:app --reload --port 8000
# ====================================================

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

from app.routers import (
    auth, users, hospitals, tourists,
    accommodations, courses, emergency, chatbot
)

app = FastAPI(
    title="K-MEDITRIP API",
    version="1.0.0",
    description="개인 의료관광객을 위한 통합 플랫폼 API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[],
    swagger_ui_parameters={"persistAuthorization": True},
)

# ── Swagger BearerAuth 설정 ────────────────────────
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi

# ── CORS 설정 ──────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 공통 에러 핸들러 ───────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": str(exc),
            "error_code": "INTERNAL_ERROR"
        }
    )

# ── 라우터 등록 ────────────────────────────────────
app.include_router(auth.router,           prefix="/api/auth",      tags=["인증"])
app.include_router(users.router,          prefix="/api/users",     tags=["사용자"])
app.include_router(hospitals.router,      prefix="/api",           tags=["병원 & 시술"])
app.include_router(tourists.router,       prefix="/api",           tags=["관광지 & 위시리스트"])
app.include_router(accommodations.router, prefix="/api",           tags=["숙소"])
app.include_router(courses.router,        prefix="/api",           tags=["코스 & 여행일정"])
app.include_router(emergency.router,      prefix="/api/emergency", tags=["긴급대응키트"])
app.include_router(chatbot.router,        prefix="/api/chatbot",   tags=["AI 챗봇"])

# ── 서버 상태 확인용 루트 엔드포인트 ──────────────
@app.get("/", tags=["상태확인"])
async def root():
    return {"message": "K-MEDITRIP API is running 🚀"}
