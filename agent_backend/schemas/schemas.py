"""
pydantic 모델: 그래프 목록 / 토폴로지 / 실행 요청의 데이터 형태를 정의한다.
/docs 스키마 문서도 여기서 자동 생성된다.
"""
from __future__ import annotations

from pydantic import BaseModel


# ---- 그래프 목록 ----
class GraphSummary(BaseModel):
    id: str
    chapter: int
    title: str
    kind: str          # "lcel" | "langgraph"
    concept: str
    input_example: dict


# ---- 토폴로지 ----
class NodeOut(BaseModel):
    id: str
    label: str
    type: str                    # "start" | "end" | "node" | "prompt" | "llm" | "parser" | "branch"
    is_conditional_target: bool
    doc: str | None = None       # 교육용 노드 해설 (opt-in)


class EdgeOut(BaseModel):
    source: str
    target: str
    conditional: bool
    condition_label: str | None
    doc: str | None = None       # 교육용 분기/전이 해설 ("{state.키}" 치환 대상)


class GraphTopology(BaseModel):
    id: str
    kind: str
    nodes: list[NodeOut]
    edges: list[EdgeOut]


# ---- 실행 요청 ----
class RunIn(BaseModel):
    input: dict = {"question": "감기 걸렸을 때 어떻게 해야 해?", "context": "", "answer": ""}


# ---- 세션 2 REST (구 session_2_agent_server 이관) ----
class TopicIn(BaseModel):
    topic: str = "LangGraph"


class QuestionIn(BaseModel):
    question: str = "Tool과 Agent의 차이를 알려줘"


class ReviewIn(BaseModel):
    review: str = "배송도 빠르고 품질도 좋아서 만족합니다."


class TextIn(BaseModel):
    text: str = "LangGraph는 State를 중심으로 노드와 엣지를 연결해 에이전트 워크플로우를 구성한다."


class TextResult(BaseModel):
    """단순 문자열 결과 (2-2 explain, 2-3 chat)."""
    result: str


class DictResult(BaseModel):
    """구조화된 dict 결과 (2-4 sentiment, 2-5 analyze)."""
    result: dict


# ---- 챕터 5: 데이트 코스 플래너 (api/date.py) ----
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
