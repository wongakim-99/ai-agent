"""
챕터 4 서비스 계층 — 로컬 우선 Multi-Agent System (MAS) 그래프.

노트북 `내_실습_LangGraph_Agent.ipynb` 4-0~4-7 을 그대로 옮겨 하나의 그래프로 조립한다.
흐름:
    entry_node (로컬에 아는 병명인가?)
      ├─ 있으면(found)  → db_agent + csv_agent (병렬 fan-out) ─┐
      └─ 없으면          → web_agent → (web_sufficient?) rag_agent ─┤
                                                                     ▼
                                                                  reporter (합류)

챕터3의 3패턴(직렬·조건분기·병렬)이 한 그래프에 전부 들어간다.
데이터 접근(disease.db/csv/RAG 문서)은 repository.py 로 분리했고, 여기서는 조회 함수만 호출한다.
모든 노드는 규칙 기반 → OPENAI_API_KEY 없이 동작한다.
"""
from __future__ import annotations

import operator
from typing import Annotated, Sequence

from typing_extensions import TypedDict
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from agent_backend.common.registry import GraphSpec, register
from agent_backend.api.chapter4 import repository
from agent_backend.api.chapter4.repository import KNOWN_DISEASES


# =========================================================
# State (노트북 4-2)
# =========================================================
class AgentState(TypedDict, total=False):
    messages: Annotated[Sequence[BaseMessage], add_messages]  # 대화 누적
    question: str            # 사용자 질문
    disease: str             # 로컬에서 찾은 병명 or "미확인"
    found: bool              # 라우팅 스위치 1 (로컬 vs fallback)
    web_sufficient: bool     # 라우팅 스위치 2 (web으로 충분 vs RAG 보강)
    # 병렬 노드가 동시에 쓰는 3키 → reducer 로 이어 붙인다
    evidence: Annotated[list[str], operator.add]
    used_agents: Annotated[list[str], operator.add]
    trace: Annotated[list[str], operator.add]


# =========================================================
# 진입 노드 + 라우터 (노트북 4-3)
# =========================================================
def _last_user_text(state: AgentState) -> str:
    if state.get("question"):
        return state["question"]
    messages = state.get("messages", [])
    return messages[-1].content if messages else ""


def _entry_node(state: AgentState):
    question = _last_user_text(state)
    disease = next((name for name in KNOWN_DISEASES if name in question), "")
    return {
        "question": question,
        "disease": disease or "미확인",
        "found": bool(disease),
        "trace": ["entry_node"],
    }


def _route_after_entry(state: AgentState):
    if state.get("found"):
        return ["db_agent", "csv_agent"]  # 리스트 → 병렬 fan-out
    return "web_agent"                    # 문자열 → 단일 이동


# =========================================================
# DB Agent + CSV Agent (노트북 4-4) — 병렬, repository 로 조회
# =========================================================
def _db_agent(state: AgentState):
    disease = state["disease"]
    row = repository.fetch_disease_db(disease)
    if not row:
        evidence = f"[DB] {disease} 데이터 없음"
    else:
        diet, exercise = row
        evidence = f"[DB] {disease}: 식단={diet}; 운동={exercise}"
    return {"evidence": [evidence], "used_agents": ["db_agent"], "trace": ["db_agent"]}


def _csv_agent(state: AgentState):
    disease = state["disease"]
    row = repository.fetch_disease_csv(disease)
    if not row:
        evidence = f"[CSV] {disease} 데이터 없음"
    else:
        evidence = f"[CSV] {disease}: 증상={row['symptom']}; 주의={row['caution']}"
    return {"evidence": [evidence], "used_agents": ["csv_agent"], "trace": ["csv_agent"]}


# =========================================================
# Web fallback + RAG Agent (노트북 4-5)
# =========================================================
def _web_agent(state: AgentState):
    """외부 검색 fallback 자리. 데모에서는 항상 RAG로 넘긴다(web_sufficient=False)."""
    return {
        "web_sufficient": False,
        "evidence": ["[Web] 회사 공유 데모에서는 외부 검색 대신 RAG Agent로 내부 문서 fallback을 수행합니다."],
        "used_agents": ["web_agent"],
        "trace": ["web_agent"],
    }


def _route_after_web(state: AgentState):
    return "reporter" if state.get("web_sufficient") else "rag_agent"


def _rag_agent(state: AgentState):
    docs = repository.retrieve_internal_docs(state["question"], k=2)
    if not docs:
        evidence = "[RAG] 관련 내부 문서를 찾지 못했습니다."
    else:
        evidence = "\n".join(f"[RAG] {doc['title']}: {doc['content']}" for doc in docs)
    return {"evidence": [evidence], "used_agents": ["rag_agent"], "trace": ["rag_agent"]}


# =========================================================
# Reporter (노트북 4-6) — 모든 경로가 합류
# =========================================================
def _reporter(state: AgentState):
    evidence = state.get("evidence", [])
    used_agents = ", ".join(state.get("used_agents", []))
    content = (
        "### 통합 건강관리 리포트\n\n"
        f"질문: {state.get('question', '')}\n\n"
        f"사용 에이전트: {used_agents}\n\n"
        "#### 수집 근거\n"
        + "\n".join(f"- {item}" for item in evidence)
        + "\n\n#### 공유 포인트\n"
        "- 정확한 로컬 키가 있으면 DB/CSV Agent가 병렬로 실행된다.\n"
        "- 로컬 키가 없으면 Web fallback을 거친 뒤 RAG Agent가 내부 문서를 검색한다.\n"
        "- Reporter는 여러 출처의 결과를 하나의 답변으로 정리한다."
    )
    return {"messages": [AIMessage(content=content)], "trace": ["reporter"]}


# =========================================================
# 그래프 조립 (노트북 4-7)
# =========================================================
def build_mas():
    b = StateGraph(AgentState)
    b.add_node("entry_node", _entry_node)
    b.add_node("db_agent", _db_agent)
    b.add_node("csv_agent", _csv_agent)
    b.add_node("web_agent", _web_agent)
    b.add_node("rag_agent", _rag_agent)
    b.add_node("reporter", _reporter)

    b.add_edge(START, "entry_node")
    b.add_conditional_edges(
        "entry_node", _route_after_entry, ["db_agent", "csv_agent", "web_agent"]
    )
    b.add_edge("db_agent", "reporter")
    b.add_edge("csv_agent", "reporter")
    b.add_conditional_edges(
        "web_agent", _route_after_web, {"rag_agent": "rag_agent", "reporter": "reporter"}
    )
    b.add_edge("rag_agent", "reporter")
    b.add_edge("reporter", END)
    return b.compile()


# =========================================================
# 레지스트리 등록
# =========================================================
register(GraphSpec(
    id="4-1", chapter=4, kind="langgraph",
    title="4-1 로컬 우선 MAS: 라우팅 + 병렬 + 합류",
    concept="entry 라우터가 로컬 키 유무로 갈라, 있으면 DB·CSV 병렬 / 없으면 web→RAG. reporter가 합류. 챕터3 3패턴을 한 그래프에 통합.",
    build=build_mas,
    input_example={
        "question": "고혈압 환자에게 맞는 식단과 운동을 알려줘",
        "evidence": [], "used_agents": [], "trace": [],
    },
    state_reducers={"evidence": "append", "used_agents": "append", "trace": "append"},
    node_types={
        "entry_node": "router",
        "db_agent": "agent", "csv_agent": "agent", "rag_agent": "agent",
        "web_agent": "fallback",
        "reporter": "reporter",
    },
    node_docs={
        "entry_node": "질문에서 아는 병명(고혈압·당뇨·비만)을 찾아 State의 disease와 found를 기록하는 라우터입니다. 여기서 이후 경로가 갈립니다.",
        "db_agent": "SQLite(disease.db)에서 식단·운동 정보를 조회합니다. csv_agent와 같은 superstep에서 병렬로 실행됩니다.",
        "csv_agent": "CSV(disease_info.csv)에서 증상·주의사항을 조회합니다. db_agent와 동시에 실행되는 병렬 일꾼입니다.",
        "web_agent": "로컬에 병명이 없을 때의 외부 검색 fallback 자리입니다. 데모에서는 항상 web_sufficient=False를 기록해 RAG로 넘깁니다.",
        "rag_agent": "내부 문서 3건을 토큰 겹침 점수로 검색해 evidence에 추가합니다. web_agent로 온 경로에서만 실행됩니다.",
        "reporter": "모든 경로가 합류하는 종착점입니다. 수집된 evidence를 모아 하나의 리포트로 정리합니다.",
    },
    edge_labels={
        "entry_node->db_agent": "found",
        "entry_node->csv_agent": "found",
        "entry_node->web_agent": "미확인",
        "web_agent->rag_agent": "웹 불충분",
        "web_agent->reporter": "웹 충분",
    },
    edge_docs={
        "entry_node->db_agent": "disease='{state.disease}'를 로컬에서 찾았기 때문에(found=true) DB·CSV 에이전트로 병렬 fan-out합니다.",
        "entry_node->csv_agent": "found=true 이므로 csv_agent도 같은 superstep에서 db_agent와 동시에 시작됩니다.",
        "entry_node->web_agent": "disease='{state.disease}'(found=false) → 로컬 데이터가 없어 웹 fallback 경로로 갑니다.",
        "web_agent->rag_agent": "web_sufficient={state.web_sufficient} → 웹만으로 부족해 내부 문서 RAG로 보강합니다.",
        "web_agent->reporter": "web_sufficient=true 이면 RAG 없이 바로 리포트로 갑니다.",
    },
))
