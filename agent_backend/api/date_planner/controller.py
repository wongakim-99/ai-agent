"""
데이트 코스 플래너 컨트롤러 — REST 라우터.

  - GET  /api/date/config     : 프론트 지도 SDK용 네이버 지도 Client ID 전달
  - POST /api/date/plan       : 그래프를 실행해 코스 결과(JSON)를 한 번에 반환
  - POST /api/date/plan/stream: 같은 실행을 SSE 로 — 노드가 끝날 때마다 진행/근거를 흘린다

/plan 과 /plan/stream 은 같은 그래프·같은 결과이고, 차이는 "중간 과정을 보여주는가" 뿐이다.
채팅 UI 는 /stream 을 쓰고, curl/스크립트는 /plan 이 편하다.
(토폴로지 뷰어의 /graphs/5-1/run 도 같은 그래프를 노드/엣지 관점으로 스트리밍한다.)

그래프는 매번 fresh 가 필요 없어 lru_cache 로 재사용한다.
"""
from functools import lru_cache
import os

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from agent_backend.common.logging_config import get_logger
from agent_backend.common.streaming import sse_frame
from agent_backend.api.date_planner import dto
from agent_backend.api.date_planner.service import build_date_course, initial_state, plan_result

router = APIRouter(prefix="/api/date", tags=["date (코스 플래너)"])
logger = get_logger(__name__)

# REST 는 토폴로지/스트리밍과 달리 fresh 그래프가 필요 없어 컴파일된 그래프를 캐시해 재사용한다.
_graph = lru_cache(build_date_course)


@router.get("/config", response_model=dto.DateConfigOut)
def config():
    """프론트 지도 표시용 네이버 지도(NCP) Client ID. (지도 표시 전용 — 도메인 제한됨)"""
    return {"naverMapsClientId": os.environ.get("NAVER_MAPS_CLIENT_ID", "")}


@router.post("/plan", response_model=dto.DatePlanOut)
def plan(body: dto.DatePlanIn):
    """자연어 요청 → 데이트 코스(실제 장소 + 순서 + 지도 마커). 한 번에 최종 결과만."""
    logger.info("date plan 요청: %r", body.question)
    final = _graph().invoke(initial_state(body.question))
    result = plan_result(final)
    logger.info("date plan 결과: region=%s, 코스 %d곳", result["region"], len(result["course"]))
    return result


@router.post("/plan/stream")
async def plan_stream(body: dto.DatePlanIn):
    """`/plan` 과 같은 실행을 SSE 로 중계한다.

    이벤트:
      step  {step: DateStep}    노드가 끝날 때마다 (병렬 노드는 끝나는 대로 각각)
      done  {result: DatePlanOut}
      error {message}

    astream(stream_mode="updates") 은 노드가 끝날 때마다 그 노드의 delta 만 준다.
    최종 State 는 안 주므로 delta 를 직접 누적해 done 을 만든다 (리듀서가 붙은 키만 이어붙임).
    """
    logger.info("date plan(stream) 요청: %r", body.question)

    async def event_stream():
        acc: dict = {"steps": []}
        try:
            async for chunk in _graph().astream(initial_state(body.question), stream_mode="updates"):
                # chunk = {노드이름: 그 노드의 delta}. 병렬 superstep 이면 여러 노드가 함께 온다.
                for delta in chunk.values():
                    for step in delta.get("steps", []):
                        yield sse_frame({"type": "step", "step": step})
                    acc["steps"] += delta.get("steps", [])
                    # region/summary/course 는 각각 한 노드만 쓰므로 덮어쓰기로 충분하다.
                    acc.update({k: v for k, v in delta.items() if k != "steps"})
            logger.info("date plan(stream) 결과: region=%s, 코스 %d곳",
                        acc.get("region"), len(acc.get("course", [])))
            yield sse_frame({"type": "done", "result": plan_result(acc)})
        except Exception as exc:  # noqa: BLE001 — 어떤 에러든 클라이언트 배너로 전달
            logger.exception("date plan(stream) 실패")
            yield sse_frame({"type": "error", "message": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",   # 프록시 버퍼링 방지
        },
    )
