"""
그래프 레지스트리: 챕터별 그래프(LCEL/LangGraph)를 하나의 목록으로 모은다.

각 기능 모듈의 service.py(api/chapterN/service.py, api/date_planner/service.py)가
자기 GraphSpec 을 register() 로 등록한다. 서버(api/graphs.py)는 list_specs()/get_spec()
으로 이 목록을 읽어 토폴로지와 실행 스트리밍을 제공한다.

새 그래프는 service.py 에서 register() 하고 이 파일 맨 아래 import 에 한 줄만
더하면 끝난다. (엔드포인트/정규화/스트리밍 무수정)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class GraphSpec:
    """그래프 하나의 메타데이터 + 빌더."""

    id: str                       # URL-safe 안정 id: "2-2", "3-1", ...
    chapter: int                  # 2 | 3 (4는 나중에)
    title: str                    # UI 제목
    kind: str                     # "lcel" | "langgraph"
    concept: str                  # UI 한 줄 개념 설명(한국어)
    build: Callable[[], Any]      # 매 호출마다 fresh 그래프/러너블을 반환하는 무인자 팩토리
    input_example: dict           # InputForm 프리필 + 초기 State/입력

    # --- LCEL 전용 ---
    # 토폴로지/스트리밍 매핑을 결정하는 모양.
    #   "single"   : llm 하나            (2-1)
    #   "linear"   : prompt→llm→parser   (2-2, 2-3, 2-4)
    #   "parallel" : start⇉branches⇉end  (2-5)
    lcel_shape: str = ""
    parser_kind: str = "str"      # "str" | "json"  (linear 노드 라벨/색에 사용)
    branches: tuple[str, ...] = ()  # parallel 브랜치 id들 예: ("summary", "keywords")

    # --- LangGraph 전용 ---
    # 병렬로 같은 key 를 쓰는 노드가 있으면 reducer 를 선언한다. 예: {"notes": "append"}
    state_reducers: dict[str, str] = field(default_factory=dict)
    # 노드 id → 역할 타입(router/agent/fallback/reporter …). 프론트 색상용.
    # 미지정 노드는 topology 에서 기본 "node" 로 폴백된다(완전 opt-in).
    node_types: dict[str, str] = field(default_factory=dict)

    # --- 교육용 나레이션 (opt-in, 없으면 프론트가 기본 문구로 폴백) ---
    node_docs: dict[str, str] = field(default_factory=dict)
    # node_id → 노드 해설(한국어). 실행 중 그 노드가 켜질 때 타임라인에 표시.
    edge_docs: dict[str, str] = field(default_factory=dict)
    # "source->target" → 분기/전이 해설. "{state.키}" 플레이스홀더는 프론트에서
    # 분기 시점의 실제 State 값으로 치환된다("왜 이 길로 갔는지").
    edge_labels: dict[str, str] = field(default_factory=dict)
    # "source->target" → 캔버스에 표시할 짧은 라벨(조건 엣지 위 칩). 타깃 id 중복 노이즈 대체.


REGISTRY: dict[str, GraphSpec] = {}


def register(spec: GraphSpec) -> None:
    REGISTRY[spec.id] = spec


def list_specs() -> list[GraphSpec]:
    """챕터·id 순으로 정렬된 spec 목록."""
    return sorted(REGISTRY.values(), key=lambda s: (s.chapter, s.id))


def get_spec(graph_id: str) -> GraphSpec:
    if graph_id not in REGISTRY:
        raise KeyError(graph_id)
    return REGISTRY[graph_id]


# 아래 import 가 각 모듈을 로드하며 register() 를 실행해 REGISTRY 를 채운다.
# (GraphSpec/register 가 위에 이미 정의돼 있어 순환 import 문제 없음)
from agent_backend.api.chapter2 import service as _ch2  # noqa: E402,F401
from agent_backend.api.chapter3 import service as _ch3  # noqa: E402,F401
from agent_backend.api.chapter4 import service as _ch4  # noqa: E402,F401
# 미니 프로젝트(date_planner)도 보너스로 토폴로지 뷰어에 5-1 로 등록된다.
from agent_backend.api.date_planner import service as _date_planner  # noqa: E402,F401
