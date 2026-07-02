"""
FastAPI 진입점: 앱을 만들고 라우터를 "등록"만 한다.
실제 엔드포인트는 routers/ 에, 데이터 형태는 schemas.py 에, 로직은 chains.py 에 있다.

실행:
    uvicorn session_2_agent_server.main:app --reload

문서(자동 생성):
    http://127.0.0.1:8000/docs
"""
from dotenv import load_dotenv
load_dotenv()  # 루트 .env 의 OPENAI_API_KEY cd 를 읽어온다. (레포 루트에서 실행 시 자동 탐색)

import time

from fastapi import FastAPI, Request

from session_2_agent_server.common.logging_config import setup_logging, get_logger
from session_2_agent_server.api import health, llm

setup_logging()                 # 앱 생성 전에 로깅을 먼저 켠다.
logger = get_logger("app")

app = FastAPI(
    title="나만의 LLM Agent 서버",
    description="노트북 섹션 2에서 배운 LCEL 체인을 API로 만든 것",
    version="0.1.0",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """모든 요청의 method/경로/상태코드/소요시간을 한 줄로 남긴다."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.0fms)",
        request.method, request.url.path, response.status_code, elapsed_ms,
    )
    return response


app.include_router(health.router)
app.include_router(llm.router)
