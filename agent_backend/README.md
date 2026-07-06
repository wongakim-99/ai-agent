# agent_backend — 통합 학습 백엔드

노트북에서 **챕터별로 배운 것들을 전부 한 패키지에 모은** FastAPI 서버.
프론트는 레포 최상위의 [`agent_frontend/`](../agent_frontend/) 와 연동된다.

| 출처 | 기능 | 엔드포인트 |
|------|------|-----------|
| 세션 2 | LCEL 체인을 REST API로 | `POST /explain` `/chat` `/sentiment` `/analyze` |
| 세션 3 | 그래프 **토폴로지 시각화 + 실행 스트리밍** | `GET /graphs`, `GET /graphs/{id}/topology`, `POST /graphs/{id}/run`(SSE) |

토폴로지 뷰어에서는:
- 노드가 실행 순서대로 **점등**되고,
- 조건분기는 **선택된 길만 밝고 안 간 길은 흐려지고(dim)**,
- 병렬은 **두 노드가 동시에** 켜지고,
- State가 **실시간으로** 채워진다 (3-3 `operator.add` reducer 병합까지 눈으로 확인).

> 왜? "LangGraph = State + 노드 + 엣지"를 눈으로 체감하고, 이후 라우터를 LLM으로 바꿔 L3 에이전트로 넘어가는 다리로 삼기 위해.

## 구조

```
agent_backend/
  main.py            FastAPI 앱 (CORS + http 로깅 + health/llm/graphs 라우터)
  api/
    health.py        GET /health
    llm.py           세션 2 REST (chapters/ch2.py 빌더 재사용)
    graphs.py        목록/토폴로지/실행SSE
  common/            registry.py, topology.py, streaming.py, llm.py, logging_config.py
  chapters/          ★ 챕터별 정리의 중심
    ch2.py           LCEL 2-1~2-5
    ch3.py           LangGraph 3-1~3-3        ← ch4.py 추가만 하면 확장
  schemas/           schemas.py
  requirements.txt

agent_frontend/      React + Vite + React Flow(@xyflow/react) + dagre  (레포 최상위)
```

핵심: 백엔드가 `graph.get_graph()`로 토폴로지를, `astream_events(v2)`로 실행 이벤트를 뽑아
**SSE**로 흘리고, 프론트가 **React Flow**로 그려 상태기계로 애니메이션한다.
(LangGraph는 안정 노드 id를 그대로 쓰고, LCEL은 역할 기반 안정 id를 부여한다.)

## 실행

**1) 백엔드** (레포 루트 `ai-agent/` 에서 — 루트 `.env`의 `OPENAI_API_KEY`를 읽는다)

```bash
# 의존성은 대부분 기존 .venv에 이미 설치돼 있음. 필요 시:
#   .venv/bin/pip install -r agent_backend/requirements.txt
.venv/bin/uvicorn agent_backend.main:app --reload
#  → http://127.0.0.1:8000/docs
```

**2) 프론트엔드**

```bash
cd agent_frontend
npm install      # 최초 1회
npm run dev
#  → http://localhost:5173   (백엔드 8000으로 프록시)
```

브라우저에서 상단의 **챕터/패턴 칩**을 고르고 입력을 넣은 뒤 **▶ 실행**을 누르면 애니메이션이 시작된다.

## API (curl)

```bash
# 세션 3 — 토폴로지/실행
curl -s localhost:8000/graphs | jq                    # 등록된 그래프 목록
curl -s localhost:8000/graphs/3-2/topology | jq       # 정규화된 노드/엣지
curl -N -X POST localhost:8000/graphs/3-2/run \
  -H 'Content-Type: application/json' \
  -d '{"input":{"disease":"고혈압","info":"","answer":""}}'   # SSE 스트림

# 세션 2 — LCEL REST
curl -s -X POST localhost:8000/explain -H 'Content-Type: application/json' -d '{"topic":"LangGraph"}'
curl -s -X POST localhost:8000/analyze -H 'Content-Type: application/json' \
  -d '{"text":"LangGraph는 State를 중심으로 노드와 엣지를 연결한다."}'
```

SSE 이벤트: `run_start → node_start / edge_taken / node_end / state (반복) → done`
(`3-2`에 `고혈압`이면 `answer_node`, `감기`면 `fallback_node`로 분기가 갈린다.)

## 등록된 그래프

| id | 챕터 | 종류 | 내용 |
|----|----|------|------|
| 2-1 | 2 | LCEL | LLM 직접 호출 (단일 노드) |
| 2-2 | 2 | LCEL | Prompt \| LLM \| StrOutputParser |
| 2-3 | 2 | LCEL | ChatPromptTemplate(system/human) |
| 2-4 | 2 | LCEL | JsonOutputParser (dict 출력) |
| 2-5 | 2 | LCEL | RunnableParallel (요약+키워드 병렬) |
| 3-1 | 3 | LangGraph | 직렬 retrieve → generate |
| 3-2 | 3 | LangGraph | 조건분기 lookup → (answer \| fallback) |
| 3-3 | 3 | LangGraph | 병렬 fan-out 후 합류 (notes reducer) |

## 챕터 4 확장 (나중에)

`chapters/ch4.py`를 만들어 MAS 그래프 빌더 + `GraphSpec`을 `register()` 하고,
`common/registry.py` 맨 아래 import에 `ch4`만 추가하면 끝. 엔드포인트/정규화/스트리밍은 무수정.
