"""
챕터 3 — LangGraph 3패턴 (직렬 / 조건분기 / 병렬).
노트북 3-1 ~ 3-3 코드를 그대로 옮겨 그래프 빌더로 만들고 레지스트리에 등록한다.
"""
from __future__ import annotations

import operator
from typing import Annotated

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

from agent_backend.common.registry import GraphSpec, register


# =========================================================
# 3-1. 직렬: retrieve → generate
# =========================================================
class SerialState(TypedDict):
    question: str
    context: str
    answer: str


def _retrieve(state: SerialState):
    question = state["question"]
    if "감기" in question:
        context = "감기에는 수분 섭취, 휴식, 따뜻한 차가 도움이 된다."
    else:
        context = "등록된 건강관리 정보가 없습니다."
    return {"context": context}


def _generate(state: SerialState):
    return {"answer": f"질문: {state['question']}\n근거: {state['context']}"}


def build_serial():
    b = StateGraph(SerialState)
    b.add_node("retrieve", _retrieve)
    b.add_node("generate", _generate)
    b.add_edge(START, "retrieve")
    b.add_edge("retrieve", "generate")
    b.add_edge("generate", END)
    return b.compile()


# =========================================================
# 3-2. 조건분기: lookup → (answer_node | fallback_node)
# =========================================================
class RouteState(TypedDict):
    disease: str
    info: str
    answer: str


_HEALTH_INFO = {
    "고혈압": "저염식, 채소와 생선 위주 식단, 가벼운 유산소 운동",
    "당뇨": "정제 탄수화물 제한, 통곡물, 식후 걷기",
}


def _lookup(state: RouteState):
    return {"info": _HEALTH_INFO.get(state["disease"], "")}


def _route_by_info(state: RouteState):
    return "answer_node" if state["info"] else "fallback_node"


def _answer_node(state: RouteState):
    return {"answer": f"{state['disease']} 관리법: {state['info']}"}


def _fallback_node(state: RouteState):
    return {"answer": f"{state['disease']} 정보는 로컬 DB에 없어 추가 검색이 필요합니다."}


def build_conditional():
    b = StateGraph(RouteState)
    b.add_node("lookup", _lookup)
    b.add_node("answer_node", _answer_node)
    b.add_node("fallback_node", _fallback_node)
    b.add_edge(START, "lookup")
    b.add_conditional_edges(
        "lookup",
        _route_by_info,
        {"answer_node": "answer_node", "fallback_node": "fallback_node"},
    )
    b.add_edge("answer_node", END)
    b.add_edge("fallback_node", END)
    return b.compile()


# =========================================================
# 3-3. 병렬: START ⇉ food_node, exercise_node ⇉ report_node
# =========================================================
class ParallelState(TypedDict):
    topic: str
    notes: Annotated[list[str], operator.add]   # reducer: 병렬 결과 이어 붙이기
    report: str


def _food_node(state: ParallelState):
    return {"notes": [f"식단 관점: {state['topic']}에는 저염식과 채소 섭취가 중요합니다."]}


def _exercise_node(state: ParallelState):
    return {"notes": [f"운동 관점: {state['topic']}에는 무리하지 않는 유산소 운동이 좋습니다."]}


def _report_node(state: ParallelState):
    return {"report": "\n".join(f"- {n}" for n in state["notes"])}


def build_parallel():
    b = StateGraph(ParallelState)
    b.add_node("food_node", _food_node)
    b.add_node("exercise_node", _exercise_node)
    b.add_node("report_node", _report_node)
    b.add_edge(START, "food_node")
    b.add_edge(START, "exercise_node")
    b.add_edge("food_node", "report_node")
    b.add_edge("exercise_node", "report_node")
    b.add_edge("report_node", END)
    return b.compile()


# =========================================================
# 레지스트리 등록
# =========================================================
register(GraphSpec(
    id="3-1", chapter=3, kind="langgraph",
    title="3-1 직렬 그래프: retrieve → generate",
    concept="add_edge 로 노드를 일렬로 잇는다. 흐름이 한 방향으로 고정된다.",
    build=build_serial,
    input_example={"question": "감기 걸렸을 때 어떻게 해야 해?", "context": "", "answer": ""},
    node_docs={
        "retrieve": "질문을 보고 관련 정보를 State의 context에 채웁니다. (여기선 규칙 기반 조회)",
        "generate": "context를 근거로 최종 answer를 만듭니다. retrieve가 끝나야 실행됩니다.",
    },
))

register(GraphSpec(
    id="3-2", chapter=3, kind="langgraph",
    title="3-2 조건분기: lookup → (answer | fallback)",
    concept="add_conditional_edges + 라우터. 실행 중 State를 보고 한쪽 길만 선택한다.",
    build=build_conditional,
    input_example={"disease": "고혈압", "info": "", "answer": ""},
    node_docs={
        "lookup": "disease로 로컬 정보(info)를 찾아 State에 기록합니다. 이 값이 다음 분기를 결정합니다.",
        "answer_node": "info가 있을 때 실행됩니다. 찾은 관리법으로 답을 만듭니다.",
        "fallback_node": "info가 비었을 때 실행됩니다. 추가 검색이 필요하다고 안내합니다.",
    },
    edge_labels={
        "lookup->answer_node": "info 있음",
        "lookup->fallback_node": "info 없음",
    },
    edge_docs={
        "lookup->answer_node": "info='{state.info}' → 로컬 정보가 있으므로 answer_node로 갑니다.",
        "lookup->fallback_node": "info가 비어 있어(로컬 정보 없음) fallback_node로 갑니다.",
    },
))

register(GraphSpec(
    id="3-3", chapter=3, kind="langgraph",
    title="3-3 병렬 fan-out 후 합류",
    concept="START에서 두 노드로 동시 분기 후 합류. notes에 operator.add reducer가 걸려 있다.",
    build=build_parallel,
    input_example={"topic": "고혈압 관리", "notes": [], "report": ""},
    state_reducers={"notes": "append"},
    node_docs={
        "food_node": "식단 관점의 메모를 notes에 추가합니다. exercise_node와 동시에 실행됩니다.",
        "exercise_node": "운동 관점의 메모를 notes에 추가합니다. food_node와 병렬로 실행됩니다.",
        "report_node": "두 병렬 노드가 모두 끝난 뒤, reducer로 합쳐진 notes를 리포트로 정리합니다.",
    },
))
