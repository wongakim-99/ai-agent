"""
라이브 검색 provider — Kakao Local API 클라이언트 (실제 장소 검색).

places.search_places() 가 이걸 먼저 시도하고, 키가 없거나 실패하면
큐레이션 데이터셋(places.DATASET)으로 폴백한다.
  - KAKAO_REST_API_KEY 가 있으면 실제 Kakao Local 키워드 검색.
  - 키가 없거나 미승인(403)/네트워크 오류면 빈 리스트를 반환(예외 안 던짐).

주의(좌표 축):
  Kakao 응답의 x = 경도(longitude), y = 위도(latitude) 이고 둘 다 "문자열"이다.
  → lat=float(y), lng=float(x) 로 바꿔서 "원시 primitive dict" 로만 담는다.
    (common/streaming.py 의 _jsonify 가 비원시 객체를 str() 로 뭉개므로,
     State/SSE 안전을 위해 dict 값은 전부 str/float 등 원시여야 한다)
"""
from __future__ import annotations

import os

import httpx

KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

# 카테고리 role → 기본 검색어 (planner 가 키워드를 안 주면 이걸 사용)
# 활동(activity)은 카테고리 코드(CT1/AT4)가 영화관 등을 일관되게 못 잡으므로 키워드 검색을 쓴다.
DEFAULT_KEYWORDS = {
    "restaurant": "맛집",
    "cafe": "카페",
    "activity": "가볼만한 곳",
}


def kakao_search(region: str, keyword: str, category: str, size: int = 8) -> list[dict]:
    """`{region} {keyword}` 로 Kakao Local 키워드 검색 → 원시 장소 dict 리스트.

    실패/무키/미승인(403) 시 예외를 던지지 않고 빈 리스트를 반환한다.
    (호출부 date_planner.places.search_places 가 빈 리스트면 큐레이션 데이터셋으로 폴백)
    스트리밍 계층에 타임아웃이 없으므로 여기서 반드시 timeout 을 건다.
    """
    query = f"{region} {keyword}".strip()
    key = os.environ.get("KAKAO_REST_API_KEY")
    if not key:
        return []

    try:
        resp = httpx.get(
            KEYWORD_URL,
            params={"query": query, "size": size},
            headers={"Authorization": f"KakaoAK {key}"},
            timeout=5.0,
        )
        resp.raise_for_status()
        docs = resp.json().get("documents", [])
    except (httpx.HTTPError, ValueError):  # 네트워크/HTTP(403 미승인 포함)/JSON 파싱 실패
        return []

    places: list[dict] = []
    for doc in docs:
        try:
            places.append(_to_place(doc, category))
        except (KeyError, ValueError, TypeError):
            continue  # 좌표가 없거나 깨진 문서는 건너뜀
    return places


def _to_place(doc: dict, category: str) -> dict:
    """Kakao document → 원시 primitive dict (JSON/State 안전)."""
    return {
        "place_name": doc["place_name"],
        "address": doc.get("road_address_name") or doc.get("address_name", ""),
        "lat": float(doc["y"]),   # Kakao y = 위도(latitude)
        "lng": float(doc["x"]),   # Kakao x = 경도(longitude)
        "url": doc.get("place_url", ""),
        "category": category,     # role: restaurant | cafe | activity
        "kakao_category": doc.get("category_name", ""),
        "phone": doc.get("phone", ""),
    }
