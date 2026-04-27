# ====================================================
#  db.py — Oracle DB 연결 & 세션 설정
#  SQLAlchemy를 통해 Oracle DB와 연결하고
#  API 라우터에서 DB를 사용할 수 있도록 세션을 제공하는 파일
# ====================================================

import oracledb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_SERVICE

# ── Oracle thick mode 설정 ─────────────────────────
# 오래된 Oracle DB 버전은 thin mode를 지원하지 않음
# thick mode로 전환해서 연결
oracledb.init_oracle_client()

# ── DB 연결 URL ────────────────────────────────────
DATABASE_URL = (
    f"oracle+oracledb://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/?service_name={DB_SERVICE}"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,          # True로 바꾸면 실행되는 SQL이 터미널에 출력됨 (디버깅용)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모든 ORM 모델의 부모 클래스
Base = declarative_base()


# ── API 라우터에서 Depends(get_db)로 호출하는 세션 함수 ──
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
