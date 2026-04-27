# ====================================================
#  services/filter.py — 시술 제약 기반 관광지 필터링
#  K-MEDITRIP 핵심 기능
#
#  동작 방식:
#  proc_id → proc_caution_map → after_caution_tag → tourist_caution
#  → 해당 관광지를 제외한 목록 반환
#
#  예시:
#  '레이저 시술' 선택 → '자외선 노출 금지' 태그 조회
#  → 해당 태그 붙은 야외 관광지 제외 → 실내 관광지만 반환
# ====================================================

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_filtered_tourists(
    db:          Session,
    proc_id:     str,
    user_id:     str,
    tour_cat1_id: str = None,
    tour_cat2_id: str = None,
    page:        int  = 0,
    size:        int  = 20,
) -> dict:
    """
    시술 제약 기반 관광지 필터링

    Args:
        db:          DB 세션
        proc_id:     시술 ID (필수)
        user_id:     찜 여부 확인용 사용자 ID
        tour_cat1_id: 대분류 필터 (선택)
        tour_cat2_id: 소분류 필터 (선택)
        page, size:  페이지네이션

    Returns:
        {applied_cautions: [태그명, ...], tourists: [...], total: int}
    """

    # ── ① 이 시술에 적용되는 주의사항 태그 조회 (배너 안내용) ──
    caut_sql = text("""
        SELECT act.after_caut_tag
        FROM proc_caution_map pcm
        JOIN after_caution_tag act
          ON pcm.after_caut_tag_id = act.after_caut_tag_id
        WHERE pcm.proc_id = :proc_id
    """)
    applied_cautions = [
        row[0] for row in db.execute(caut_sql, {"proc_id": proc_id}).fetchall()
    ]

    # ── ② 카테고리 필터 조건 동적 생성 ───────────────────────
    cat_filter = ""
    params: dict = {"proc_id": proc_id, "user_id": user_id,
                    "offset": page * size, "size": size}

    if tour_cat2_id:
        cat_filter = "AND t.tour_cat2_id = :tour_cat2_id"
        params["tour_cat2_id"] = tour_cat2_id
    elif tour_cat1_id:
        cat_filter = "AND tc2.tour_cat1_id = :tour_cat1_id"
        params["tour_cat1_id"] = tour_cat1_id

    # ── ③ 제약 걸리는 관광지를 제외한 목록 조회 ──────────────
    tour_sql = text(f"""
        SELECT
            t.tour_id,
            t.tour_name,
            t.addr,
            t.img_url,
            t.lat,
            t.lon,
            tc1.tour_cat1_name,
            tc2.tour_cat2_name,
            CASE WHEN tw.tour_id IS NOT NULL THEN 1 ELSE 0 END AS is_wished
        FROM tourist t
        JOIN tourist_category_2 tc2 ON t.tour_cat2_id = tc2.tour_cat2_id
        JOIN tourist_category_1 tc1 ON tc2.tour_cat1_id = tc1.tour_cat1_id
        LEFT JOIN tourist_wishlist tw
               ON t.tour_id = tw.tour_id AND tw.user_id = :user_id
        WHERE t.tour_id NOT IN (
            SELECT tc.tour_id
            FROM tourist_caution tc
            JOIN proc_caution_map pcm
              ON tc.after_caut_tag_id = pcm.after_caut_tag_id
            WHERE pcm.proc_id = :proc_id
        )
        {cat_filter}
        ORDER BY t.tour_name
        OFFSET :offset ROWS FETCH NEXT :size ROWS ONLY
    """)

    # ④ 전체 개수 조회
    count_sql = text(f"""
        SELECT COUNT(*)
        FROM tourist t
        JOIN tourist_category_2 tc2 ON t.tour_cat2_id = tc2.tour_cat2_id
        WHERE t.tour_id NOT IN (
            SELECT tc.tour_id
            FROM tourist_caution tc
            JOIN proc_caution_map pcm
              ON tc.after_caut_tag_id = pcm.after_caut_tag_id
            WHERE pcm.proc_id = :proc_id
        )
        {cat_filter}
    """)

    tourists_raw = db.execute(tour_sql, params).fetchall()
    total = db.execute(count_sql, params).scalar()

    tourists = []
    for row in tourists_raw:
        r = dict(row._mapping)
        r["is_wished"] = bool(r.get("is_wished"))
        tourists.append(r)

    return {
        "applied_cautions": applied_cautions,
        "tourists":         tourists,
        "total":            total,
    }
