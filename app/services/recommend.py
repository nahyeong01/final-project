# ====================================================
#  services/recommend.py — AI 코스 자동 추천 로직
#
#  MODE A (풀 모드): 5가지 고려사항 전체 적용
#    ① 시술 후 제약 관광지 제외
#    ② 찜한 관광지 소분류 기반 취향
#    ③ 같은 시술 유저 행동 기반 취향 (proc_recommendation_cache)
#    ④ 같은 국적 유저 행동 기반 취향 (nation_recommendation_cache)
#    ⑤ 숙소 기준 가까운 관광지 순 동선 최적화 (Haversine)
#
#  MODE B (부분 모드): 입력된 항목에 해당하는 고려사항만 적용
#  MODE C (랜덤 모드): 관광 일정 + 찜한 관광지만 → 국적 기반 랜덤 추천
# ====================================================

from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional
import random

from app.services.haversine import haversine


def recommend_course(
    db:        Session,
    user_id:   str,
    trip_id:   str,
    proc_id:   Optional[str] = None,
    nation_id: Optional[str] = None,
    acc_lat:   Optional[float] = None,
    acc_lon:   Optional[float] = None,
    seed:      Optional[int]   = None,
) -> list:
    """
    AI 코스 자동 추천

    Args:
        db:        DB 세션
        user_id:   현재 사용자 ID
        trip_id:   여행 일정 ID
        proc_id:   선택한 시술 ID (없으면 제약 필터 미적용)
        nation_id: 국적 ID (없으면 국적 추천 미적용)
        acc_lat/lon: 숙소 좌표 (없으면 거리 최적화 미적용)
        seed:      새로고침용 랜덤 시드

    Returns:
        days: [{day, date, spots: [...]}, ...]
    """
    if seed:
        random.seed(seed)

    # ── 여행 일정 조회 ─────────────────────────────
    trip = db.execute(
        text("SELECT trip_start, trip_end FROM user_trip WHERE trip_id = :id"),
        {"id": trip_id}
    ).fetchone()

    if not trip:
        return []

    trip_start: date = trip[0].date() if hasattr(trip[0], 'date') else trip[0]
    trip_end:   date = trip[1].date() if hasattr(trip[1], 'date') else trip[1]
    total_days = (trip_end - trip_start).days + 1

    # ── 후보 관광지 쿼리 구성 ─────────────────────
    # 기본: 전체 관광지. 시술이 있으면 제약 관광지 제외
    exclusion = ""
    params: dict = {"user_id": user_id}

    if proc_id:
        exclusion = """
            AND t.tour_id NOT IN (
                SELECT tc.tour_id FROM tourist_caution tc
                JOIN proc_caution_map pcm
                  ON tc.after_caut_tag_id = pcm.after_caut_tag_id
                WHERE pcm.proc_id = :proc_id
            )
        """
        params["proc_id"] = proc_id

    # ── 추천 점수 계산 ────────────────────────────
    # 기본 점수 = proc 추천 점수 + nation 추천 점수 + 찜 가중치
    score_join = ""
    score_select = "0 AS score_p, 0 AS score_a"

    if proc_id:
        score_join += """
            LEFT JOIN proc_recommedation_cache prc
                   ON t.tour_id = prc.tour_id AND prc.proc_id = :proc_id
        """
        score_select = "COALESCE(prc.score_p, 0) AS score_p"
        if nation_id:
            score_join += """
                LEFT JOIN nation_recommendation_cache nrc
                       ON t.tour_id = nrc.tour_id AND nrc.nation_id = :nation_id
            """
            score_select += ", COALESCE(nrc.score_a, 0) AS score_a"
            params["nation_id"] = nation_id
        else:
            score_select += ", 0 AS score_a"

    candidates_sql = text(f"""
        SELECT
            t.tour_id, t.tour_name, t.addr, t.img_url,
            t.lat, t.lon,
            tc1.tour_cat1_name, tc2.tour_cat2_name,
            {score_select},
            CASE WHEN tw.tour_id IS NOT NULL THEN 3 ELSE 0 END AS wish_bonus
        FROM tourist t
        JOIN tourist_category_2 tc2 ON t.tour_cat2_id = tc2.tour_cat2_id
        JOIN tourist_category_1 tc1 ON tc2.tour_cat1_id = tc1.tour_cat1_id
        LEFT JOIN tourist_wishlist tw ON t.tour_id = tw.tour_id AND tw.user_id = :user_id
        {score_join}
        WHERE 1=1 {exclusion}
        FETCH FIRST 200 ROWS ONLY
    """)

    candidates = [dict(r._mapping) for r in db.execute(candidates_sql, params).fetchall()]

    # ── 최종 점수 계산 & 정렬 ─────────────────────
    for c in candidates:
        base_score = float(c.get("score_p") or 0) + float(c.get("score_a") or 0)
        wish_bonus = float(c.get("wish_bonus") or 0)

        # 숙소 기준 거리 점수 (가까울수록 높은 점수)
        dist_score = 0
        if acc_lat and acc_lon and c.get("lat") and c.get("lon"):
            dist_km = haversine(acc_lat, acc_lon, float(c["lat"]), float(c["lon"]))
            dist_score = max(0, 10 - dist_km)   # 10km 이내 가산점

        c["_final_score"] = base_score + wish_bonus + dist_score + random.uniform(0, 0.5)

    candidates.sort(key=lambda x: x["_final_score"], reverse=True)

    # ── 일차별 배분 ───────────────────────────────
    spots_per_day = 4   # 하루 4곳 기준
    days = []

    for i in range(total_days):
        day_spots = candidates[i * spots_per_day: (i + 1) * spots_per_day]
        spots = []
        for order, spot in enumerate(day_spots, start=1):
            spots.append({
                "tour_id":     spot["tour_id"],
                "tour_name":   spot["tour_name"],
                "visit_order": order,
                "addr":        spot.get("addr"),
                "img_url":     spot.get("img_url"),
                "lat":         float(spot["lat"]) if spot.get("lat") else None,
                "lon":         float(spot["lon"]) if spot.get("lon") else None,
            })

        days.append({
            "day":   i + 1,
            "date":  trip_start + timedelta(days=i),
            "spots": spots,
        })

    return days
