"""
데이트 코스 플래너 REST 라우터 (제품용, 비-SSE).

  - GET  /api/date/config : 프론트 지도 SDK용 네이버 지도 Client ID 전달
  - POST /api/date/plan   : 그래프를 실행해 코스 결과(JSON)를 한 번에 반환

토폴로지 뷰어의 /graphs/5-1/run(SSE)과 "같은 그래프"를 쓰지만, 여기서는 최종 결과만 준다.
그래프는 매번 fresh 가 필요 없어 lru_cache 로 재사용한다 (api/llm.py 패턴).
"""
from functools import lru_cache
import os

from fastapi import APIRouter

from agent_backend.api.date_planner import schemas
from agent_backend.api.date_planner.graph import build_date_course
from agent_backend.common.logging_config import get_logger

router = APIRouter(prefix="/api/date", tags=["date (코스 플래너)"])
logger = get_logger(__name__)

# REST 는 토폴로지/스트리밍과 달리 fresh 그래프가 필요 없어 컴파일된 그래프를 캐시해 재사용한다.
_graph = lru_cache(build_date_course)


@router.get("/config", response_model=schemas.DateConfigOut)
def config():
    """프론트 지도 표시용 네이버 지도(NCP) Client ID. (지도 표시 전용 — 도메인 제한됨)"""
    return {"naverMapsClientId": os.environ.get("NAVER_MAPS_CLIENT_ID", "")}


@router.post("/plan", response_model=schemas.DatePlanOut)
def plan(body: schemas.DatePlanIn):
    """자연어 요청 → 데이트 코스(실제 장소 + 순서 + 지도 마커)."""
    logger.info("date plan 요청: %r", body.question)
    final = _graph().invoke(
        {"question": body.question, "places": [], "searched": [], "trace": []}
    )
    course = final.get("course", [])
    # 지도 마커용 평면 목록 (코스 스텝과 1:1)
    places = [
        {k: c.get(k) for k in ("place_name", "address", "lat", "lng", "url", "category")}
        for c in course
    ]
    logger.info("date plan 결과: region=%s, 코스 %d곳", final.get("region"), len(course))
    return {
        "region": final.get("region", ""),
        "summary": final.get("summary", ""),
        "course": course,
        "places": places,
    }
