# ====================================================
#  services/haversine.py — GPS 거리 계산
#  두 GPS 좌표 사이의 실제 거리(km)를 계산하는 함수
#  응급실 목록 거리순 정렬, 숙소 반경 필터링에 사용
# ====================================================

from math import radians, sin, cos, sqrt, atan2


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Haversine 공식으로 두 GPS 좌표 간 거리(km) 계산

    사용 예시:
        dist = haversine(37.49, 127.03, 37.50, 127.04)
        → 약 1.4 km 반환

    Args:
        lat1, lon1: 출발지 위도/경도
        lat2, lon2: 도착지 위도/경도

    Returns:
        두 지점 간 거리 (km, 소수점 2자리)
    """
    R = 6371.0  # 지구 반지름 (km)

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (sin(dlat / 2) ** 2
         + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2)

    return round(R * 2 * atan2(sqrt(a), sqrt(1 - a)), 2)
