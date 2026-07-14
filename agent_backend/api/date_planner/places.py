"""
큐레이션 장소 데이터셋 + 통합 검색 (데이트 코스 에이전트용).

외부 실시간 API(카카오/네이버/구글)는 전부 결제·심사 벽이 있어서, 실습/데모용으로는
"실제 서울 장소를 미리 조사해 코드에 넣어두는" 큐레이션 데이터셋을 기본값으로 쓴다.
(챕터4의 로컬 disease.db 와 같은 발상 — 실제 데이터를 로컬에 보관)

핵심: `search_places()` 는 카카오 키가 있고 실제 응답이 오면 그걸 쓰고(라이브),
없거나 실패하면 데이터셋으로 폴백한다. → 카카오 심사가 통과되면 코드 수정 없이 자동 라이브.

주의: 지도는 네이버 지도를 쓰므로 좌표는 WGS84 위경도(lat/lng)면 된다.
      장소 dict 는 원시값만 담는다(streaming._jsonify 안전).
"""
from __future__ import annotations

import os
from urllib.parse import quote

from agent_backend.api.date_planner.providers import kakao_search


# =========================================================
# 큐레이션 데이터셋 — 실제 서울 데이트 장소 (인기 지역 위주)
# region: 사용자가 흔히 말하는 '거점' 이름 / category: restaurant|cafe|activity
# 좌표는 동네 단위로 실제에 가깝게. (대표 큐레이션 샘플이라 전 지역/실시간은 아님)
# =========================================================
DATASET: list[dict] = [
    # ---------------- 홍대 / 연남 / 합정 (마포) ----------------
    {"region": "홍대", "category": "restaurant", "place_name": "을밀대", "address": "서울 마포구 숭문길 24", "lat": 37.5476, "lng": 126.9447},
    {"region": "홍대", "category": "restaurant", "place_name": "툭툭누들타이 연남점", "address": "서울 마포구 동교로 246", "lat": 37.5624, "lng": 126.9256},
    {"region": "홍대", "category": "cafe", "place_name": "앤트러사이트 합정점", "address": "서울 마포구 토정로5길 10", "lat": 37.5487, "lng": 126.9138},
    {"region": "홍대", "category": "cafe", "place_name": "커피리브레 연남점", "address": "서울 마포구 성미산로 198", "lat": 37.5620, "lng": 126.9250},
    {"region": "홍대", "category": "activity", "place_name": "경의선숲길 연남동", "address": "서울 마포구 연남동", "lat": 37.5606, "lng": 126.9255},
    {"region": "홍대", "category": "activity", "place_name": "홍대 걷고싶은거리", "address": "서울 마포구 어울마당로", "lat": 37.5546, "lng": 126.9236},

    # ---------------- 성수 (성동) ----------------
    {"region": "성수", "category": "restaurant", "place_name": "브루클린더버거조인트 성수", "address": "서울 성동구 성수이로", "lat": 37.5450, "lng": 127.0556},
    {"region": "성수", "category": "restaurant", "place_name": "성수족발", "address": "서울 성동구 성수동", "lat": 37.5440, "lng": 127.0562},
    {"region": "성수", "category": "cafe", "place_name": "대림창고 갤러리카페", "address": "서울 성동구 성수이로 78", "lat": 37.5433, "lng": 127.0559},
    {"region": "성수", "category": "cafe", "place_name": "어니언 성수", "address": "서울 성동구 아차산로9길 8", "lat": 37.5447, "lng": 127.0578},
    {"region": "성수", "category": "activity", "place_name": "서울숲", "address": "서울 성동구 뚝섬로 273", "lat": 37.5444, "lng": 127.0374},
    {"region": "성수", "category": "activity", "place_name": "언더스탠드에비뉴", "address": "서울 성동구 왕십리로 63", "lat": 37.5423, "lng": 127.0448},

    # ---------------- 강남 / 삼성 (강남) ----------------
    {"region": "강남", "category": "restaurant", "place_name": "농민백암순대 강남본점", "address": "서울 강남구 강남대로98길", "lat": 37.4996, "lng": 127.0273},
    {"region": "강남", "category": "restaurant", "place_name": "하동관 강남점", "address": "서울 강남구 강남대로", "lat": 37.5010, "lng": 127.0246},
    {"region": "강남", "category": "cafe", "place_name": "테라로사 포스코센터점", "address": "서울 강남구 테헤란로 440", "lat": 37.5068, "lng": 127.0586},
    {"region": "강남", "category": "cafe", "place_name": "블루보틀 삼성", "address": "서울 강남구 영동대로", "lat": 37.5108, "lng": 127.0596},
    {"region": "강남", "category": "activity", "place_name": "코엑스 별마당도서관", "address": "서울 강남구 영동대로 513", "lat": 37.5127, "lng": 127.0590},
    {"region": "강남", "category": "activity", "place_name": "봉은사", "address": "서울 강남구 봉은사로 531", "lat": 37.5148, "lng": 127.0577},

    # ---------------- 이태원 / 한남 (용산) ----------------
    {"region": "이태원", "category": "restaurant", "place_name": "라이너스 바베큐 이태원", "address": "서울 용산구 이태원로", "lat": 37.5344, "lng": 126.9946},
    {"region": "이태원", "category": "restaurant", "place_name": "바토스 이태원", "address": "서울 용산구 이태원로", "lat": 37.5340, "lng": 126.9925},
    {"region": "이태원", "category": "cafe", "place_name": "패션5 한남", "address": "서울 용산구 한남대로 272", "lat": 37.5341, "lng": 127.0018},
    {"region": "이태원", "category": "cafe", "place_name": "테일러커피 이태원", "address": "서울 용산구 이태원로", "lat": 37.5343, "lng": 126.9948},
    {"region": "이태원", "category": "activity", "place_name": "리움미술관", "address": "서울 용산구 이태원로55길 60-16", "lat": 37.5385, "lng": 127.0047},
    {"region": "이태원", "category": "activity", "place_name": "남산서울타워", "address": "서울 용산구 남산공원길 105", "lat": 37.5512, "lng": 126.9882},

    # ---------------- 종로 / 삼청 / 안국 (종로) ----------------
    {"region": "종로", "category": "restaurant", "place_name": "삼청동수제비", "address": "서울 종로구 삼청로 101-1", "lat": 37.5843, "lng": 126.9812},
    {"region": "종로", "category": "restaurant", "place_name": "광장시장 먹자골목", "address": "서울 종로구 창경궁로 88", "lat": 37.5701, "lng": 126.9997},
    {"region": "종로", "category": "cafe", "place_name": "어니언 안국", "address": "서울 종로구 계동길 5", "lat": 37.5765, "lng": 126.9855},
    {"region": "종로", "category": "cafe", "place_name": "레이어드 안국", "address": "서울 종로구 북촌로2길", "lat": 37.5773, "lng": 126.9840},
    {"region": "종로", "category": "activity", "place_name": "경복궁", "address": "서울 종로구 사직로 161", "lat": 37.5796, "lng": 126.9770},
    {"region": "종로", "category": "activity", "place_name": "국립현대미술관 서울", "address": "서울 종로구 삼청로 30", "lat": 37.5787, "lng": 126.9800},
    {"region": "종로", "category": "activity", "place_name": "북촌한옥마을", "address": "서울 종로구 계동길", "lat": 37.5826, "lng": 126.9850},

    # ---------------- 여의도 (영등포) ----------------
    {"region": "여의도", "category": "restaurant", "place_name": "bills 여의도 (더현대 서울)", "address": "서울 영등포구 여의대로 108", "lat": 37.5259, "lng": 126.9286},
    {"region": "여의도", "category": "cafe", "place_name": "노티드 여의도 (더현대 서울)", "address": "서울 영등포구 여의대로 108", "lat": 37.5259, "lng": 126.9285},
    {"region": "여의도", "category": "activity", "place_name": "여의도한강공원", "address": "서울 영등포구 여의동로 330", "lat": 37.5285, "lng": 126.9327},
    {"region": "여의도", "category": "activity", "place_name": "더현대 서울", "address": "서울 영등포구 여의대로 108", "lat": 37.5259, "lng": 126.9285},
    {"region": "여의도", "category": "activity", "place_name": "63스퀘어", "address": "서울 영등포구 63로 50", "lat": 37.5197, "lng": 126.9403},
]


def _region_match(req: str, entry: dict) -> bool:
    """느슨한 지역 매칭: 거점 이름이 서로 포함되거나, 요청 지역이 주소에 있으면 매칭."""
    region = entry["region"]
    return (req in region) or (region in req) or (req in entry["address"])


def curated_search(region: str, keyword: str, category: str, size: int = 8) -> list[dict]:
    """데이터셋에서 카테고리 + 지역으로 필터링해 장소 dict 리스트를 반환한다."""
    pool = [p for p in DATASET if p["category"] == category]
    matched = [p for p in pool if _region_match(region, p)]
    picked = matched or pool  # 해당 지역이 없으면 카테고리 전체에서라도 제공(코스가 비지 않게)
    return [_to_place(p) for p in picked[:size]]


def _to_place(p: dict) -> dict:
    """데이터셋 항목 → 표준 장소 dict (원시값만). url 은 네이버 지도 검색 링크로 생성."""
    return {
        "place_name": p["place_name"],
        "address": p["address"],
        "lat": p["lat"],
        "lng": p["lng"],
        "url": f"https://map.naver.com/p/search/{quote(p['place_name'])}",
        "category": p["category"],
        "kakao_category": p.get("kakao_category", ""),
        "phone": "",
    }


def search_places(region: str, keyword: str, category: str, size: int = 8) -> list[dict]:
    """통합 검색: 카카오 라이브가 되면 그걸, 아니면 큐레이션 데이터셋을 쓴다.

    → 카카오맵 심사가 통과돼 KAKAO_REST_API_KEY 가 실제로 동작하면 코드 수정 없이 자동 라이브 전환.
    """
    if os.environ.get("KAKAO_REST_API_KEY"):
        live = kakao_search(region=region, keyword=keyword, category=category, size=size)
        if live:  # 승인 전에는 403 → [] 이므로 아래 데이터셋으로 폴백
            return live
    return curated_search(region, keyword, category, size)
