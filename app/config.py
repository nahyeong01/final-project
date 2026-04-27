# ====================================================
#  config.py — 환경변수 로드
#  .env 파일의 값을 읽어서 앱 전체에서 사용할 수 있게 해주는 파일
# ====================================================

from dotenv import load_dotenv
import os

load_dotenv()

# Oracle DB
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT", "1521")
DB_SERVICE  = os.getenv("DB_SERVICE")

# JWT
JWT_SECRET            = os.getenv("JWT_SECRET")
JWT_ALGORITHM         = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_EXPIRE_HOURS = int(os.getenv("JWT_ACCESS_EXPIRE_HOURS", "24"))
JWT_REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))

# 카카오 API
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")

# OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
