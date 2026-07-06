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
))

register(GraphSpec(
    id="3-2", chapter=3, kind="langgraph",
    title="3-2 조건분기: lookup → (answer | fallback)",
    concept="add_conditional_edges + 라우터. 실행 중 State를 보고 한쪽 길만 선택한다.",
    build=build_conditional,
    input_example={"disease": "고혈압", "info": "", "answer": ""},
))

register(GraphSpec(
    id="3-3", chapter=3, kind="langgraph",
    title="3-3 병렬 fan-out 후 합류",
    concept="START에서 두 노드로 동시 분기 후 합류. notes에 operator.add reducer가 걸려 있다.",
    build=build_parallel,
    input_example={"topic": "고혈압 관리", "notes": [], "report": ""},
    state_reducers={"notes": "append"},
))
