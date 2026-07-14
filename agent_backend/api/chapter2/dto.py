"""
챕터 2 DTO — LCEL REST 엔드포인트의 요청/응답 pydantic 모델.
(구 schemas/schemas.py 의 세션2 모델을 이 모듈로 분리)
"""
from __future__ import annotations

from pydantic import BaseModel


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
