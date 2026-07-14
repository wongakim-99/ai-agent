"""
FastAPI 진입점: 앱을 만들고 라우터를 등록한다.

통합 백엔드: 챕터별 학습 결과물 + 미니 프로젝트가 여기에 모인다.
  - api/llm.py     : 세션 2 — LCEL 체인을 REST API 로 (/explain /chat /sentiment /analyze)
  - api/graphs.py  : 세션 3 — 그래프 토폴로지 + 실행 SSE (/graphs...)
  - api/chapters/     : 챕터별 그래프/체인 정의 (ch2, ch3, ch4)
  - api/date_planner/ : 데이트 코스 AI Agent 미니 프로젝트 (/api/date/*, 토폴로지 5-1)

실행 (레포 루트에서):
    uvicorn agent_backend.main:app --reload

문서:
    http://127.0.0.1:8000/docs
프론트엔드(dev):
    cd agent_frontend && npm run dev   # http://localhost:5173
"""
from dotenv import load_dotenv
load_dotenv()  # 레포 루트 .env 의 OPENAI_API_KEY 를 chapters import 전에 읽는다.

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from agent_backend.common.logging_config import setup_logging, get_logger
from agent_backend.api import health, llm, graphs
from agent_backend.api.date_planner.router import router as date_router

setup_logging()
logger = get_logger("app")

app = FastAPI(
    title="Agent Backend — 통합 학습 서버",
    description=(
        "노트북에서 배운 것들을 챕터별로 모은 백엔드. "
        "세션 2: LCEL 체인 REST API(/explain 등), "
        "세션 3: 그래프 토폴로지 시각화 + 실행 스트리밍(/graphs)."
    ),
    version="0.2.0",
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
app.include_router(llm.router)
app.include_router(graphs.router)
app.include_router(date_router)  # date_planner 미니 프로젝트 (/api/date/*)
