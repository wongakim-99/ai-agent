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


class DatePlanOut(BaseModel):
    region: str
    summary: str
    course: list[CourseStop]
    places: list[MapPlace]


class DateConfigOut(BaseModel):
    """프론트 지도 표시용 네이버 지도(NCP) Client ID (도메인 제한 공개키)."""
    naverMapsClientId: str
