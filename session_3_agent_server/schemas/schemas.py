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


class EdgeOut(BaseModel):
    source: str
    target: str
    conditional: bool
    condition_label: str | None


class GraphTopology(BaseModel):
    id: str
    kind: str
    nodes: list[NodeOut]
    edges: list[EdgeOut]


# ---- 실행 요청 ----
class RunIn(BaseModel):
    input: dict = {"question": "감기 걸렸을 때 어떻게 해야 해?", "context": "", "answer": ""}
