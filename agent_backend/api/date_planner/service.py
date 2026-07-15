"""
데이트 코스 플래너 서비스 계층 — LLM + 실제 장소 기반 Multi-Agent System 그래프.

흐름:
    planner (LLM: 지역·의도 파싱 + 검색할 카테고리/키워드 결정)
      ├─ restaurant_agent ┐
      ├─ cafe_agent       ├─ (병렬) 장소 실검색 (repository.search_places)
      └─ activity_agent   ┘
                          ▼
                       curator (LLM: 실제 후보로 순서 있는 코스 큐레이션)

챕터4의 로컬 우선 MAS 구조(router → 병렬 fan-out → reporter 합류)를 데이트 도메인으로 옮긴 것.
다른 점:
  - 라우팅/큐레이션에 실제 LLM 을 쓴다 (OPENAI_API_KEY 필요).
  - 장소는 큐레이션 데이터셋(카카오 승인 시 라이브)에서 실제로 가져온다 (환각 방지).
  - curator LLM 은 place_id + 시간대 + 이유만 만들고, 장소 사실정보(이름/좌표/주소)는
    코드가 실제 검색 결과에서 조인한다.

같은 그래프가 `POST /api/date/plan`(제품용, controller.py)과 토폴로지 뷰어 `5-1`(SSE) 둘 다에서 재사용된다.

각 노드는 결과뿐 아니라 `steps` 에 "무엇을 왜 결정했는지"를 한 조각씩 남긴다.
컨트롤러가 이걸 SSE 로 흘려서 채팅 UI 가 에이전트의 진행 상황을 실시간으로 보여준다.
근거 문장은 코드가 실제 값으로 조립하므로(LLM 재호출 없음) 비용이 들지 않고 항상 사실과 일치한다.
"""
from __future__ import annotations

import operator
from typing import Annotated

from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

from agent_backend.common.registry import GraphSpec, register
from agent_backend.common.llm import get_llm
from agent_backend.api.date_planner.repository import (
    DEFAULT_KEYWORDS,
    SOURCE_LABEL,
    search_places_with_source,
)


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
    steps: Annotated[list[dict], operator.add]   # 노드별 진행/근거 (UI 스트리밍용)
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
_CATEGORY_LABEL = {"restaurant": "맛집", "cafe": "카페", "activity": "활동"}
# 지역 파싱 규칙 기반 폴백용 (LLM 이 지역을 못 뽑을 때만 사용)
_KNOWN_REGIONS = [
    "홍대", "강남", "성수", "이태원", "연남", "합정", "건대",
    "신촌", "여의도", "종로", "명동", "잠실", "가로수길", "삼청동",
]


# =========================================================
# 진행 상황 조각 (steps)
# =========================================================
def _step(node: str, kind: str, title: str, lines: list[str]) -> dict:
    """UI 가 그대로 그릴 수 있는 진행 조각. kind 는 아이콘/색 선택에만 쓰인다.

    원시값만 담는다 (common/streaming._jsonify 와 SSE 직렬화 양쪽에 안전).
    """
    return {"node": node, "kind": kind, "title": title, "lines": lines}


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
    region_by_rule = not region
    if region_by_rule:  # LLM 이 지역을 못 뽑으면 규칙 기반 폴백
        region = next((r for r in _KNOWN_REGIONS if r in question), "서울")

    plan: dict = {}
    if parsed.restaurant_keyword.strip():
        plan["restaurant"] = parsed.restaurant_keyword.strip()
    if parsed.cafe_keyword.strip():
        plan["cafe"] = parsed.cafe_keyword.strip()
    if parsed.activity_keyword.strip():
        plan["activity"] = parsed.activity_keyword.strip()
    plan_by_default = not plan
    if plan_by_default:  # 아무 카테고리도 안 잡히면 기본 데이트 코스(식사+카페)
        plan = {
            "restaurant": DEFAULT_KEYWORDS["restaurant"],
            "cafe": DEFAULT_KEYWORDS["cafe"],
        }

    agents_to_run = [_AGENT_BY_CATEGORY[c] for c in plan]
    intent = parsed.intent.strip() or "장소 추천"

    return {
        "question": question,
        "region": region,
        "intent": intent,
        "plan": plan,
        "agents_to_run": agents_to_run,
        "trace": ["planner"],
        "steps": [_planner_step(region, region_by_rule, intent, plan, plan_by_default, agents_to_run)],
    }


def _planner_step(
    region: str, region_by_rule: bool, intent: str,
    plan: dict, plan_by_default: bool, agents_to_run: list[str],
) -> dict:
    """planner 가 무엇을 어떻게 정했는지 — 지역·의도·검색 계획·분기."""
    lines = [
        f"지역: {region}" + (" (LLM이 못 뽑아 요청 문장에서 규칙으로 찾음)" if region_by_rule else ""),
        f"의도: {intent}",
    ]
    lines += [
        f"{_CATEGORY_LABEL[cat]} 검색어 → '{kw}'"
        for cat, kw in plan.items()
    ]
    if plan_by_default:
        lines.append("카테고리를 하나도 못 잡아 기본 코스(식사+카페)로 되돌림")
    lines.append(f"→ {', '.join(agents_to_run)} {len(agents_to_run)}개를 병렬로 실행")
    return _step("planner", "planner", "요청 분석 · 검색 계획 결정", lines)


def _route_after_planner(state: DateState):
    """실행할 검색 에이전트 목록(리스트 반환) → 병렬 fan-out."""
    return state.get("agents_to_run") or ["restaurant_agent"]


# =========================================================
# 검색 에이전트 (노트북 4-4) — 병렬, 각자 실검색
# =========================================================
def _search_agent(state: DateState, category: str, node_name: str):
    region = state.get("region", "서울")
    keyword = state.get("plan", {}).get(category) or DEFAULT_KEYWORDS[category]
    places, source = search_places_with_source(
        region=region, keyword=keyword, category=category, size=8
    )

    lines = [f"'{region} {keyword}' 검색 → {len(places)}곳", f"출처: {SOURCE_LABEL[source]}"]
    if places:  # 뒤의 curator 가 무엇 중에서 골랐는지 보이도록 후보 이름을 남긴다
        lines.append("후보: " + ", ".join(p["place_name"] for p in places))
    else:
        lines.append("결과 없음 — 이 카테고리는 코스에서 빠집니다")

    return {
        "places": places,
        "searched": [node_name],
        "trace": [node_name],
        "steps": [_step(node_name, "search", f"{_CATEGORY_LABEL[category]} 검색", lines)],
    }


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
            "steps": [_step("curator", "curator", "코스 큐레이션", ["후보 장소가 0곳이라 코스를 만들 수 없음"])],
        }

    # 실제 후보를 인덱싱해서 LLM 에 제시 (LLM 은 place_id 만 고른다 → 환각 방지)
    catalog = "\n".join(
        f"[{i}] ({p.get('category')}) {p.get('place_name')} | "
        f"{p.get('kakao_category', '')} | {p.get('address', '')}"
        for i, p in enumerate(places)
    )

    llm = get_llm().with_structured_output(CoursePlan)
    llm_error = ""
    try:
        plan: CoursePlan = llm.invoke(
            "너는 데이트 코스 큐레이터야. 아래 '실제' 후보 장소들 중에서 골라 시간 순서가 있는 "
            "데이트 코스를 만들어줘. 반드시 주어진 place_id 만 사용하고, 없는 장소를 지어내지 마. "
            "보통 식사→카페→활동 흐름이 좋지만 요청 분위기에 맞춰 조정해.\n\n"
            f"요청: {question}\n의도: {intent}\n\n후보 목록:\n{catalog}"
        )
        stops, summary = plan.stops, plan.summary
    except Exception as exc:  # noqa: BLE001 — LLM/파싱 실패 시 결정론적 폴백
        stops, summary, llm_error = [], "", str(exc)

    course = _build_course(stops, places)
    used_fallback = not course
    if used_fallback:  # LLM 이 비었거나 전부 무효 → 카테고리별 1곳 순서 배치
        course = _fallback_course(places)
        summary = summary or f"{state.get('region', '')} 데이트 코스입니다."

    return {
        "summary": summary,
        "course": course,
        "trace": ["curator"],
        "steps": [_curator_step(places, stops, course, used_fallback, llm_error)],
    }


def _curator_step(
    places: list[dict], stops: list, course: list[dict], used_fallback: bool, llm_error: str,
) -> dict:
    """curator 가 후보 몇 곳 중 무엇을 왜 골랐는지 — 폴백으로 샌 경우 그 이유까지."""
    lines = [f"검색 결과 {len(places)}곳이 모두 합류 → 이 중에서만 고름 (없는 장소 지어내기 방지)"]
    if llm_error:
        lines.append(f"LLM 큐레이션 실패({llm_error}) → 규칙 기반 코스로 대체")
    elif used_fallback:
        dropped = len(stops)
        lines.append(
            f"LLM이 고른 {dropped}곳이 전부 무효한 place_id → 규칙 기반 코스로 대체"
            if dropped else "LLM이 아무 장소도 고르지 않음 → 규칙 기반 코스로 대체"
        )
    elif len(stops) > len(course):
        lines.append(f"LLM이 {len(stops)}곳을 골랐고, 무효/중복 id {len(stops) - len(course)}곳을 걸러냄")

    if used_fallback:
        lines.append("규칙: 카테고리별 첫 장소를 맛집 → 카페 → 활동 순으로 배치")
    lines += [f"{c['step']}. {c['place_name']} ({c['time_slot']}) — {c['reason']}" for c in course]
    return _step("curator", "curator", f"코스 큐레이션 · {len(course)}곳 선정", lines)


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
# 그래프 입출력 헬퍼 (controller 의 REST/SSE 양쪽이 공유)
# =========================================================
def initial_state(question: str) -> dict:
    """리듀서가 붙은 키는 빈 리스트로 시작해야 한다 (operator.add 대상)."""
    return {"question": question, "places": [], "searched": [], "trace": [], "steps": []}


def plan_result(final: dict) -> dict:
    """최종 State → DatePlanOut 모양. 지도 마커는 코스 스텝과 1:1 로 뽑는다."""
    course = final.get("course", [])
    return {
        "region": final.get("region", ""),
        "summary": final.get("summary", ""),
        "course": course,
        "places": [
            {k: c.get(k) for k in ("place_name", "address", "lat", "lng", "url", "category")}
            for c in course
        ],
        "steps": final.get("steps", []),
    }


# =========================================================
# 레지스트리 등록 (보너스: 학습 토폴로지 뷰어에 5-1 로 노출)
# =========================================================
register(GraphSpec(
    id="5-1", chapter=5, kind="langgraph",
    title="5-1 POI 추천 파이프라인: planner → 병렬 검색 → curator",
    concept=(
        "planner(LLM)가 지역·의도를 파싱해 검색 에이전트를 병렬 fan-out하고, 각 에이전트가 "
        "실제 장소를 가져오면 curator(LLM)가 순서 있는 동선으로 큐레이션한다."
    ),
    build=build_date_course,
    input_example={
        "question": "홍대 저녁 식사 · 조용한 카페 동선",
        "places": [], "searched": [], "trace": [], "steps": [],
    },
    state_reducers={"places": "append", "searched": "append", "trace": "append", "steps": "append"},
    node_types={
        "planner": "router",
        "restaurant_agent": "agent", "cafe_agent": "agent", "activity_agent": "agent",
        "curator": "reporter",
    },
    node_docs={
        "planner": "요청에서 지역·분위기를 파악하고 어떤 카테고리(맛집/카페/활동)를 검색할지 정하는 라우터입니다. 여기서 병렬 경로가 갈립니다.",
        "restaurant_agent": "맛집을 검색합니다. 다른 검색 에이전트와 같은 superstep에서 병렬로 실행됩니다.",
        "cafe_agent": "카페를 검색합니다. 병렬 일꾼입니다.",
        "activity_agent": "볼거리·활동(전시/영화관 등)을 검색합니다.",
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
