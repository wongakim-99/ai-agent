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


# 이 파일은 그래프 뷰어 프레임워크(api/graphs.py) 전용 DTO만 둔다.
# 기능별 요청/응답 DTO 는 각 모듈로 분리됨:
#   - 챕터2 LCEL REST : api/chapter2/dto.py (TopicIn, QuestionIn, TextResult ...)
#   - 데이트 플래너    : api/date_planner/dto.py (DatePlanIn, DatePlanOut ...)
