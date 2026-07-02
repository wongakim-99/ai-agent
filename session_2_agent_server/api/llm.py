"""
LLM 라우터: 섹션 2에서 배운 체인 4개를 엔드포인트로 노출한다.
로직(chains) 과 데이터 형태(schemas) 를 가져다 "연결만" 하는 얇은 층이다.
"""
from fastapi import APIRouter

from session_2_agent_server.schemas import schemas
from session_2_agent_server.common.logging_config import get_logger
from session_2_agent_server.common.chains import (
    explain_chain,
    chat_chain,
    sentiment_chain,
    analyze_chain,
)

router = APIRouter(tags=["llm"])
logger = get_logger(__name__)   # name = session_2_agent_server.api.llm


@router.post("/explain", response_model=schemas.TextResult)
def explain(body: schemas.TopicIn):
    """2-2. LCEL: 주제를 3문장으로 설명."""
    logger.info("explain 요청: topic=%r", body.topic)
    return {"result": explain_chain().invoke({"topic": body.topic})}


@router.post("/chat", response_model=schemas.TextResult)
def chat(body: schemas.QuestionIn):
    """2-3. 역할(강사) 프롬프트로 답변."""
    logger.info("chat 요청: question=%r", body.question)
    return {"result": chat_chain().invoke({"question": body.question})}


@router.post("/sentiment", response_model=schemas.DictResult)
def sentiment(body: schemas.ReviewIn):
    """2-4. 문장 감정 분석을 JSON(dict)으로 반환."""
    logger.info("sentiment 요청: review 길이=%d자", len(body.review))
    result = sentiment_chain().invoke({"review": body.review})
    logger.info("sentiment 결과: %s", result)
    return {"result": result}


@router.post("/analyze", response_model=schemas.DictResult)
def analyze(body: schemas.TextIn):
    """2-5. 요약 + 키워드를 병렬로 동시에 뽑아 반환."""
    logger.info("analyze 요청: text 길이=%d자", len(body.text))
    return {"result": analyze_chain().invoke({"text": body.text})}
