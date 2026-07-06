"""
FastAPI 진입점: 앱을 만들고 라우터를 등록한다. (session_2 관례 + CORS/스트리밍 확장)

실행 (레포 루트에서):
    uvicorn session_3_agent_server.main:app --reload

문서:
    http://127.0.0.1:8000/docs
프론트엔드(dev):
    cd session_3_agent_server/frontend && npm run dev   # http://localhost:5173
"""
from dotenv import load_dotenv
load_dotenv()  # 레포 루트 .env 의 OPENAI_API_KEY 를 chapters import 전에 읽는다.

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from session_3_agent_server.common.logging_config import setup_logging, get_logger
from session_3_agent_server.api import health, graphs

setup_logging()
logger = get_logger("app")

app = FastAPI(
    title="LangGraph 토폴로지 실행 뷰어",
    description="노트북 챕터 2(LCEL)·3(LangGraph)의 그래프를 토폴로지로 그리고 실행을 애니메이션한다.",
    version="0.1.0",
)

# 프론트(Vite dev, 5173)에서 백엔드(8000)로 직접 호출할 때를 위한 CORS.
# (Vite proxy 를 쓰면 same-origin 이지만, 직접 curl/비프록시 테스트를 위해 열어둔다)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(graphs.router)
