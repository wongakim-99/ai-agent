"""
pydantic 모델 모음: 요청(Request) / 응답(Response) 의 "데이터 형태"를 정의한다.
- 엔드포인트는 여기 정의된 형태로 입력을 검증받고, 여기 형태로 응답을 내보낸다.
- /docs 의 스키마 문서도 이 클래스들에서 자동 생성된다.
"""
from pydantic import BaseModel


# ---- 요청(Request) 모델: 클라이언트가 보내는 body 형태 ----
class TopicIn(BaseModel):
    topic: str = "LangGraph"


class QuestionIn(BaseModel):
    question: str = "Tool과 Agent의 차이를 알려줘"


class ReviewIn(BaseModel):
    review: str = "배송도 빠르고 품질도 좋아서 만족합니다."


class TextIn(BaseModel):
    text: str = "LangGraph는 State를 중심으로 노드와 엣지를 연결해 에이전트 워크플로우를 구성한다."


# ---- 응답(Response) 모델: 서버가 돌려주는 형태 ----
class TextResult(BaseModel):
    """단순 문자열 결과 (2-2 explain, 2-3 chat)."""
    result: str


class DictResult(BaseModel):
    """구조화된 dict 결과 (2-4 sentiment, 2-5 analyze)."""
    result: dict
