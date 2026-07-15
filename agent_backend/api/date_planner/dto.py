"""
date_planner DTO — REST 입출력 pydantic 모델.

챕터 스키마(agent_backend/schemas/schemas.py)와 분리해 이 기능 모듈 안에 둔다.
/docs 스키마 문서도 여기서 자동 생성된다.
"""
from __future__ import annotations

from pydantic import BaseModel


class DatePlanIn(BaseModel):
    question: str = "홍대에서 조용한 저녁 데이트 코스 짜줘, 카페 좋아해"


class CourseStop(BaseModel):
    """코스의 한 스텝 (시간 순서 있는 방문 장소)."""
    step: int
    time_slot: str           # "저녁 6시" 등
    category: str            # restaurant | cafe | activity
    place_name: str
    address: str
    lat: float | None = None
    lng: float | None = None
    url: str
    reason: str


class MapPlace(BaseModel):
    """지도 마커용 평면 장소 (코스 스텝 N == 마커 N)."""
    place_name: str
    address: str
    lat: float | None = None
    lng: float | None = None
    url: str
    category: str


class DateStep(BaseModel):
    """에이전트 한 노드가 무엇을 왜 했는지 (진행 상황 표시용).

    문장은 백엔드가 실제 값으로 조립한다 → LLM 추가 호출 없이 항상 사실과 일치.
    """
    node: str                # planner | restaurant_agent | cafe_agent | activity_agent | curator
    kind: str                # planner | search | curator — UI 아이콘/색 선택용
    title: str               # "맛집 검색"
    lines: list[str]         # 결정 근거 문장들


class DatePlanOut(BaseModel):
    region: str
    summary: str
    course: list[CourseStop]
    places: list[MapPlace]
    steps: list[DateStep] = []   # 노드별 진행/근거 (SSE 로 먼저 흐르고, 최종 응답에도 함께 담긴다)


class DateConfigOut(BaseModel):
    """프론트 지도 표시용 네이버 지도(NCP) Client ID (도메인 제한 공개키)."""
    naverMapsClientId: str
