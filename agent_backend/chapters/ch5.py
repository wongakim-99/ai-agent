"""
챕터 5 — 데이트 코스 플래너 (LLM + 실제 장소 기반 Multi-Agent System).

흐름:
    planner (LLM: 지역·의도 파싱 + 검색할 카테고리/키워드 결정)
      ├─ restaurant_agent ┐
      ├─ cafe_agent       ├─ (병렬) Kakao Local 실검색
      └─ activity_agent   ┘
                          ▼
                       curator (LLM: 실제 후보로 순서 있는 코스 큐레이션)

챕터4의 로컬 우선 MAS 구조(router → 병렬 fan-out → reporter 합류)를 데이트 도메인으로 옮긴 것.
다른 점:
  - 라우팅/큐레이션에 실제 LLM 을 쓴다 (OPENAI_API_KEY 필요).
  - 장소는 Kakao Local API 에서 실제로 가져온다 (환각 방지).
  - curator LLM 은 place_id + 시간대 + 이유만 만들고, 장소 사실정보(이름/좌표/주소)는
    코드가 실제 검색 결과에서 조인한다.

같은 그래프가 `POST /api/date/plan`(제품용)과 토폴로지 뷰어 `5-1`(SSE) 둘 다에서 재사용된다.
"""
from __future__ import annotations

import operator
from typing import Annotated

from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

from agent_backend.common.registry import GraphSpec, register
from agent_backend.common.llm import get_llm
from agent_backend.common.kakao import kakao_search, DEFAULT_KEYWORDS


# =========================================================
# State (노트북 4-2 패턴)
# =========================================================
class DateState(TypedDict, total=False):
    question: str                          # 사용자 자연어 요청
    region: str                            # planner 가 파싱한 지역 (예: "홍대")
    intent: str                            # planner 가 요약한 분위기/의도
    plan: dict                             # {category: 검색어}
    agents_to_run: list[str]               # 라우터가 읽는 "실행할 노드" 목록
    # 병렬 노드가 동시에 쓰는 키 → operator.add 리듀서로 이어붙임 (state_reducers 에도 선언)
    places: Annotated[list[dict], operator.add]
    searched: Annotated[list[str], operator.add]
    trace: Annotated[list[str], operator.add]
    summary: str                           # curator 작성
    course: list[dict]                     # curator 작성 (순서 있는 코스)


# =========================================================
# LLM 구조화 출력 스키마
# =========================================================
class PlannerOut(BaseModel):
    """planner LLM 출력: 요청에서 지역/의도/카테고리별 검색어를 뽑는다."""
    region: str = Field(description="데이트 지역명. 예: 홍대, 강남, 성수. 불명확하면 빈 문자열.")
    intent: str = Field(description="분위기/의도 한 줄 요약. 예: 조용한 저녁 데이트")
    restaurant_keyword: str = Field(default="", description="맛집 검색어(예: 조용한 이탈리안). 식사 불필요하면 빈 문자열.")
    cafe_keyword: str = Field(default="", description="카페 검색어(예: 감성 카페). 불필요하면 빈 문자열.")
    activity_keyword: str = Field(default="", description="활동/볼거리 검색어(예: 전시, 영화관). 불필요하면 빈 문자열.")


class Stop(BaseModel):
    place_id: int = Field(description="주어진 후보 목록의 place_id (0부터 시작). 목록에 있는 값만 사용.")
    time_slot: str = Field(description="시간대. 예: 저녁 6시, 식사 후, 오후")
    reason: str = Field(description="이 장소를 이 순서에 넣은 이유(한국어 한두 문장).")


class CoursePlan(BaseModel):
    """curator LLM 출력: 실제 후보들로 짠 순서 있는 코스."""
    summary: str = Field(description="코스 전체를 소개하는 2~3문장 요약(한국어).")
    stops: list[Stop] = Field(description="시간 순서대로 정렬된 방문 장소들.")


# 카테고리 role ↔ 노드 이름
_AGENT_BY_CATEGORY = {
    "restaurant": "restaurant_agent",
    "cafe": "cafe_agent",
    "activity": "activity_agent",
}
# 지역 파싱 규칙 기반 폴백용 (LLM 이 지역을 못 뽑을 때만 사용)
_KNOWN_REGIONS = [
    "홍대", "강남", "성수", "이태원", "연남", "합정", "건대",
    "신촌", "여의도", "종로", "명동", "잠실", "가로수길", "삼청동",
]


# =========================================================
# 진입 노드 + 라우터 (노트북 4-3)
# =========================================================
def _planner_node(state: DateState):
    """LLM 구조화 출력으로 지역·의도·카테고리별 검색어를 파싱한다."""
    question = state.get("question", "") or ""
    llm = get_llm().with_structured_output(PlannerOut)
    parsed: PlannerOut = llm.invoke(
        "너는 데이트 코스 플래너의 라우터야. 사용자 요청에서 데이트 지역과 분위기를 파악하고, "
        "어떤 장소들을 검색할지 카테고리별 검색어를 정해줘.\n"
        "데이트 코스는 보통 2~3곳으로 구성된다: 식사(맛집) → 카페 → (선택) 활동(전시/영화/산책 등).\n"
        "규칙:\n"
        "- '저녁/점심/식사/밥' 같은 식사 맥락이 있으면 restaurant_keyword를 반드시 채운다.\n"
        "- 카페를 원하거나 일반적인 데이트면 cafe_keyword도 채운다.\n"
        "- 전시/영화/공연/산책 등 활동 의도가 보이면 activity_keyword도 채운다.\n"
        "- 사용자의 분위기 선호(예: 조용한, 감성적인)를 검색어에 반영한다.\n"
        "- 정말 관련 없는 카테고리만 빈 문자열로 둔다. 되도록 최소 2개 카테고리는 채운다.\n\n"
        f"요청: {question}"
    )

    region = parsed.region.strip()
    if not region:  # LLM 이 지역을 못 뽑으면 규칙 기반 폴백
        region = next((r for r in _KNOWN_REGIONS if r in question), "서울")

    plan: dict = {}
    if parsed.restaurant_keyword.strip():
        plan["restaurant"] = parsed.restaurant_keyword.strip()
    if parsed.cafe_keyword.strip():
        plan["cafe"] = parsed.cafe_keyword.strip()
    if parsed.activity_keyword.strip():
        plan["activity"] = parsed.activity_keyword.strip()
    if not plan:  # 아무 카테고리도 안 잡히면 기본 데이트 코스(식사+카페)
        plan = {
            "restaurant": DEFAULT_KEYWORDS["restaurant"],
            "cafe": DEFAULT_KEYWORDS["cafe"],
        }

    agents_to_run = [_AGENT_BY_CATEGORY[c] for c in plan]

    return {
        "question": question,
        "region": region,
        "intent": parsed.intent.strip() or "데이트 코스",
        "plan": plan,
        "agents_to_run": agents_to_run,
        "trace": ["planner"],
    }


def _route_after_planner(state: DateState):
    """실행할 검색 에이전트 목록(리스트 반환) → 병렬 fan-out."""
    return state.get("agents_to_run") or ["restaurant_agent"]


# =========================================================
# 검색 에이전트 (노트북 4-4) — 병렬, 각자 Kakao 실검색
# =========================================================
def _search_agent(state: DateState, category: str, node_name: str):
    region = state.get("region", "서울")
    keyword = state.get("plan", {}).get(category) or DEFAULT_KEYWORDS[category]
    places = kakao_search(region=region, keyword=keyword, category=category, size=8)
    return {"places": places, "searched": [node_name], "trace": [node_name]}


def _restaurant_agent(state: DateState):
    return _search_agent(state, "restaurant", "restaurant_agent")


def _cafe_agent(state: DateState):
    return _search_agent(state, "cafe", "cafe_agent")


def _activity_agent(state: DateState):
    return _search_agent(state, "activity", "activity_agent")


# =========================================================
# Curator (노트북 4-6) — 합류, 실제 후보로 코스 큐레이션
# =========================================================
def _curator_node(state: DateState):
    places: list[dict] = state.get("places", [])
    question = state.get("question", "")
    intent = state.get("intent", "")

    if not places:
        return {
            "summary": "조건에 맞는 장소를 찾지 못했어요. 지역이나 키워드를 바꿔서 다시 시도해 주세요.",
            "course": [],
            "trace": ["curator"],
        }

    # 실제 후보를 인덱싱해서 LLM 에 제시 (LLM 은 place_id 만 고른다 → 환각 방지)
    catalog = "\n".join(
        f"[{i}] ({p.get('category')}) {p.get('place_name')} | "
        f"{p.get('kakao_category', '')} | {p.get('address', '')}"
        for i, p in enumerate(places)
    )

    llm = get_llm().with_structured_output(CoursePlan)
    try:
        plan: CoursePlan = llm.invoke(
            "너는 데이트 코스 큐레이터야. 아래 '실제' 후보 장소들 중에서 골라 시간 순서가 있는 "
            "데이트 코스를 만들어줘. 반드시 주어진 place_id 만 사용하고, 없는 장소를 지어내지 마. "
            "보통 식사→카페→활동 흐름이 좋지만 요청 분위기에 맞춰 조정해.\n\n"
            f"요청: {question}\n의도: {intent}\n\n후보 목록:\n{catalog}"
        )
        stops, summary = plan.stops, plan.summary
    except Exception:  # noqa: BLE001 — LLM/파싱 실패 시 결정론적 폴백
        stops, summary = [], ""

    course = _build_course(stops, places)
    if not course:  # LLM 이 비었거나 전부 무효 → 카테고리별 1곳 순서 배치
        course = _fallback_course(places)
        summary = summary or f"{state.get('region', '')} 데이트 코스입니다."

    return {"summary": summary, "course": course, "trace": ["curator"]}


def _build_course(stops: list, places: list[dict]) -> list[dict]:
    """LLM stops(place_id+시간대+이유) → 실제 장소 사실정보와 조인. 무효/중복 id 는 drop."""
    n = len(places)
    seen: set[int] = set()
    course: list[dict] = []
    for stop in stops:
        pid = stop.place_id
        if not (0 <= pid < n) or pid in seen:
            continue
        seen.add(pid)
        course.append(_course_entry(len(course) + 1, stop.time_slot, places[pid], stop.reason))
        if len(course) >= 5:
            break
    return course


def _fallback_course(places: list[dict]) -> list[dict]:
    """카테고리별 첫 장소를 restaurant→cafe→activity 순으로 배치(결정론적)."""
    slots = {"restaurant": "식사", "cafe": "카페 타임", "activity": "활동"}
    course: list[dict] = []
    for cat in ("restaurant", "cafe", "activity"):
        p = next((x for x in places if x.get("category") == cat), None)
        if p:
            course.append(_course_entry(len(course) + 1, slots[cat], p, "추천 장소입니다."))
    return course


def _course_entry(step: int, time_slot: str, p: dict, reason: str) -> dict:
    """코스 한 스텝 dict. 장소 사실정보는 전부 실제 place dict 에서 온다."""
    return {
        "step": step,
        "time_slot": time_slot,
        "category": p.get("category", ""),
        "place_name": p.get("place_name", ""),
        "address": p.get("address", ""),
        "lat": p.get("lat"),
        "lng": p.get("lng"),
        "url": p.get("url", ""),
        "reason": reason,
    }


# =========================================================
# 그래프 조립 (노트북 4-7)
# =========================================================
def build_date_course():
    b = StateGraph(DateState)
    b.add_node("planner", _planner_node)
    b.add_node("restaurant_agent", _restaurant_agent)
    b.add_node("cafe_agent", _cafe_agent)
    b.add_node("activity_agent", _activity_agent)
    b.add_node("curator", _curator_node)

    b.add_edge(START, "planner")
    b.add_conditional_edges(
        "planner", _route_after_planner,
        ["restaurant_agent", "cafe_agent", "activity_agent"],
    )
    b.add_edge("restaurant_agent", "curator")
    b.add_edge("cafe_agent", "curator")
    b.add_edge("activity_agent", "curator")
    b.add_edge("curator", END)
    return b.compile()


# =========================================================
# 레지스트리 등록
# =========================================================
register(GraphSpec(
    id="5-1", chapter=5, kind="langgraph",
    title="5-1 데이트 코스 플래너: planner → 병렬 검색 → curator",
    concept=(
        "planner(LLM)가 지역·의도를 파싱해 검색 에이전트를 병렬 fan-out하고, 각 에이전트가 "
        "Kakao 로컬에서 실제 장소를 가져오면 curator(LLM)가 순서 있는 코스로 큐레이션한다."
    ),
    build=build_date_course,
    input_example={
        "question": "홍대에서 조용한 저녁 데이트 코스 짜줘, 카페 좋아해",
        "places": [], "searched": [], "trace": [],
    },
    state_reducers={"places": "append", "searched": "append", "trace": "append"},
    node_types={
        "planner": "router",
        "restaurant_agent": "agent", "cafe_agent": "agent", "activity_agent": "agent",
        "curator": "reporter",
    },
    node_docs={
        "planner": "요청에서 지역·분위기를 파악하고 어떤 카테고리(맛집/카페/활동)를 검색할지 정하는 라우터입니다. 여기서 병렬 경로가 갈립니다.",
        "restaurant_agent": "Kakao 로컬에서 맛집을 검색합니다. 다른 검색 에이전트와 같은 superstep에서 병렬로 실행됩니다.",
        "cafe_agent": "Kakao 로컬에서 카페를 검색합니다. 병렬 일꾼입니다.",
        "activity_agent": "Kakao 로컬에서 볼거리·활동(전시/영화관 등)을 검색합니다.",
        "curator": "모든 검색 결과가 합류하는 종착점입니다. 실제 장소들만으로 시간 순서가 있는 데이트 코스를 큐레이션합니다.",
    },
    edge_labels={
        "planner->restaurant_agent": "맛집",
        "planner->cafe_agent": "카페",
        "planner->activity_agent": "액티비티",
    },
    edge_docs={
        "planner->restaurant_agent": "'{state.region}' 요청에 식사가 포함돼 restaurant_agent로 병렬 fan-out합니다.",
        "planner->cafe_agent": "카페 선호가 감지돼 cafe_agent가 같은 superstep에서 동시에 시작됩니다.",
        "planner->activity_agent": "관람/활동 의도가 있어 activity_agent도 병렬 실행됩니다.",
    },
))
