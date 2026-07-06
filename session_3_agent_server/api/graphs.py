"""
그래프 라우터: 목록 / 토폴로지 / 실행(SSE) 3개 엔드포인트.
로직(registry/topology/streaming)을 가져다 연결만 하는 얇은 층이다.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from session_3_agent_server.schemas import schemas
from session_3_agent_server.common.logging_config import get_logger
from session_3_agent_server.common.registry import list_specs, get_spec
from session_3_agent_server.common.topology import build_topology
from session_3_agent_server.common.streaming import run_events

router = APIRouter(tags=["graphs"])
logger = get_logger(__name__)


def _sse(event: dict) -> str:
    """이벤트 dict → SSE 프레임 (data: 한 줄, \\n\\n 종단)."""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.get("/graphs", response_model=list[schemas.GraphSummary])
def list_graphs():
    """등록된 모든 그래프 요약. (프론트의 챕터/패턴 선택기가 이걸 읽는다)"""
    return [
        schemas.GraphSummary(
            id=s.id, chapter=s.chapter, title=s.title,
            kind=s.kind, concept=s.concept, input_example=s.input_example,
        )
        for s in list_specs()
    ]


@router.get("/graphs/{graph_id}/topology", response_model=schemas.GraphTopology)
def topology(graph_id: str):
    """그래프의 정규화된 노드/엣지 토폴로지."""
    try:
        spec = get_spec(graph_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"그래프 없음: {graph_id}")
    return build_topology(spec)


@router.post("/graphs/{graph_id}/run")
async def run(graph_id: str, body: schemas.RunIn):
    """그래프를 실행하며 노드/엣지/State 이벤트를 SSE 로 스트리밍한다."""
    try:
        spec = get_spec(graph_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"그래프 없음: {graph_id}")

    logger.info("run %s: input keys=%s", graph_id, list(body.input.keys()))

    async def event_stream():
        try:
            async for ev in run_events(spec, body.input):
                yield _sse(ev)
        except Exception as exc:  # noqa: BLE001 — 어떤 에러든 클라이언트에 전달
            logger.exception("run %s 실패", graph_id)
            yield _sse({"type": "error", "message": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",   # 프록시 버퍼링 방지
        },
    )
