"""
세션 2 — LCEL 체인 REST 라우터. (구 session_2_agent_server/api/llm.py 를 통합 이관)
체인을 여기서 중복 정의하지 않고 chapters/ch2.py 의 빌더를 재사용한다.
빌더는 매번 fresh 러너블을 만들므로, REST 용도로는 @lru_cache 로 한 번만 만들어 캐시한다.
"""
from functools import lru_cache

from fastapi import APIRouter

from agent_backend.schemas import schemas
from agent_backend.common.logging_config import get_logger
from agent_backend.chapters.ch2 import (
    build_explain,
    build_chat,
    build_sentiment,
    build_analyze,
)

router = APIRouter(tags=["llm (세션 2)"])
logger = get_logger(__name__)

# REST 는 토폴로지/스트리밍과 달리 fresh 그래프가 필요 없어 러너블을 캐시해 재사용한다.
_explain = lru_cache(build_explain)
_chat = lru_cache(build_chat)
_sentiment = lru_cache(build_sentiment)
_analyze = lru_cache(build_analyze)


@router.post("/explain", response_model=schemas.TextResult)
def explain(body: schemas.TopicIn):
    """2-2. LCEL: 주제를 3문장으로 설명."""
    logger.info("explain 요청: topic=%r", body.topic)
    return {"result": _explain().invoke({"topic": body.topic})}


@router.post("/chat", response_model=schemas.TextResult)
def chat(body: schemas.QuestionIn):
    """2-3. 역할(강사) 프롬프트로 답변."""
    logger.info("chat 요청: question=%r", body.question)
    return {"result": _chat().invoke({"question": body.question})}


@router.post("/sentiment", response_model=schemas.DictResult)
def sentiment(body: schemas.ReviewIn):
    """2-4. 문장 감정 분석을 JSON(dict)으로 반환."""
    logger.info("sentiment 요청: review 길이=%d자", len(body.review))
    result = _sentiment().invoke({"review": body.review})
    logger.info("sentiment 결과: %s", result)
    return {"result": result}


@router.post("/analyze", response_model=schemas.DictResult)
def analyze(body: schemas.TextIn):
    """2-5. 요약 + 키워드를 병렬로 동시에 뽑아 반환."""
    logger.info("analyze 요청: text 길이=%d자", len(body.text))
    return {"result": _analyze().invoke({"text": body.text})}
