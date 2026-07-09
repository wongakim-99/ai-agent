"""
그래프 실행을 astream_events(v2) 로 돌리며 프론트 친화적 이벤트 dict 를 yield 한다.
api/graphs.py 가 이걸 SSE 프레임으로 감싸 브라우저로 흘린다.

이벤트 타입:
  run_start   {graph_id}
  node_start  {node}
  token       {node, text}          # LLM 토큰 (선택)
  node_end    {node, delta}         # 그 노드가 바꾼 State/출력
  edge_taken  {source, target, conditional, condition_label}
  state       {state}               # 병합된 현재 State 스냅샷
  done        {state}               # 최종 State/출력
  error       {message, node?}
"""
from __future__ import annotations

from typing import Any, AsyncIterator

from langchain_core.messages import BaseMessage

from agent_backend.common.topology import build_topology


# ---------------------------------------------------------
# 직렬화 헬퍼: 메시지/기타 객체를 JSON 가능한 형태로
# ---------------------------------------------------------
def _jsonify(obj: Any) -> Any:
    if isinstance(obj, BaseMessage):
        return obj.content
    if isinstance(obj, dict):
        return {k: _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonify(v) for v in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


# =========================================================
# LangGraph
# =========================================================
async def _run_langgraph(spec, input_state: dict) -> AsyncIterator[dict]:
    graph = spec.build()
    topo = build_topology(spec)

    incoming: dict[str, list[dict]] = {}
    outgoing: dict[str, list[dict]] = {}
    for e in topo["edges"]:
        incoming.setdefault(e["target"], []).append(e)
        outgoing.setdefault(e["source"], []).append(e)

    reducers = spec.state_reducers
    state: dict[str, Any] = dict(input_state)

    # superstep 레이어 추적 — 실제로 "탄" 엣지만 강조하기 위함.
    # LangGraph 는 BSP(superstep) 단위로 노드를 실행한다. 한 노드가 시작될 때,
    # "직전 superstep 에서 실제로 끝난 노드(prev_layer)" → 이 노드로 가는 엣지만이
    # 진짜 탄 엣지다. 그래서 incoming 을 전부 강조하지 않고 prev_layer 로 필터한다.
    #  · 조건부 fan-out(entry→db,csv): 두 노드가 같은 superstep → 둘 다 강조 ✓
    #  · 경로 의존 fan-in(reporter): 실제 실행된 선행자에서 온 엣지만 강조 ✓
    #    (예: web→reporter 는 web 이 rag 로 갔으면 강조되지 않음)
    prev_layer: set[str] = {"__start__"}
    cur_layer: set[str] = set()
    in_flight = 0

    yield {"type": "run_start", "graph_id": spec.id}

    async for ev in graph.astream_events(input_state, version="v2"):
        etype = ev["event"]
        name = ev.get("name")
        meta = ev.get("metadata") or {}
        lgn = meta.get("langgraph_node")

        # 루트(LangGraph) 종료 → 전체 최종 State
        if lgn is None and name == "LangGraph" and etype == "on_chain_end":
            final = ev.get("data", {}).get("output")
            if isinstance(final, dict):
                state = _jsonify(final)
            yield {"type": "done", "state": state}
            continue

        # 진짜 노드 경계만: name == langgraph_node (라우터 함수는 name != lgn 이라 걸러짐)
        if name != lgn:
            continue

        if etype == "on_chain_start":
            # in_flight 가 0 인데 이전 layer 가 있으면 새 superstep 시작 → layer 회전
            if in_flight == 0 and cur_layer:
                prev_layer = cur_layer
                cur_layer = set()
            cur_layer.add(name)
            in_flight += 1
            # prev_layer(실제 실행된 직전 노드) 에서 온 엣지만 "탄" 것으로 강조
            for e in incoming.get(name, []):
                if e["source"] in prev_layer:
                    yield {"type": "edge_taken", "source": e["source"], "target": e["target"],
                           "conditional": e["conditional"], "condition_label": e["condition_label"]}
            yield {"type": "node_start", "node": name}

        elif etype == "on_chain_end":
            in_flight -= 1
            delta = ev.get("data", {}).get("output")
            if not isinstance(delta, dict):
                delta = {}
            for k, v in delta.items():
                if reducers.get(k) == "append":
                    state[k] = (state.get(k) or []) + list(v)
                else:
                    state[k] = v
            yield {"type": "node_end", "node": name, "delta": _jsonify(delta)}
            # 이 노드에서 END 로 가는 엣지 강조
            for e in outgoing.get(name, []):
                if e["target"] == "__end__":
                    yield {"type": "edge_taken", "source": name, "target": "__end__",
                           "conditional": e["conditional"], "condition_label": e["condition_label"]}
            yield {"type": "state", "state": _jsonify(state)}


# =========================================================
# LCEL
# =========================================================
def _lcel_node_of(etype: str) -> str | None:
    """linear/single 체인에서 이벤트 타입 → 안정 노드 id."""
    if "prompt" in etype:
        return "prompt"
    if "chat_model" in etype:
        return "llm"
    if "parser" in etype:
        return "parser"
    return None


def _content(obj: Any) -> Any:
    if isinstance(obj, BaseMessage):
        return obj.content
    return _jsonify(obj)


async def _run_lcel_linear(spec, input_data: dict, order: list[str]) -> AsyncIterator[dict]:
    """single(llm) / linear(prompt→llm→parser)."""
    runnable = spec.build()
    yield {"type": "run_start", "graph_id": spec.id}

    # single 은 llm 에 원문 문자열을 그대로 준다.
    model_input: Any = list(input_data.values())[0] if spec.lcel_shape == "single" else input_data

    seen: set[str] = set()
    final_output: Any = None

    async for ev in runnable.astream_events(model_input, version="v2"):
        etype = ev["event"]
        nid = _lcel_node_of(etype)
        if nid is None or nid not in order:
            continue

        if etype.endswith("_start") and nid not in seen:
            seen.add(nid)
            idx = order.index(nid)
            src = "__start__" if idx == 0 else order[idx - 1]
            yield {"type": "edge_taken", "source": src, "target": nid,
                   "conditional": False, "condition_label": None}
            yield {"type": "node_start", "node": nid}

        elif etype.endswith("_stream") and nid == "llm":
            chunk = ev.get("data", {}).get("chunk")
            text = getattr(chunk, "content", "") or ""
            if text:
                yield {"type": "token", "node": "llm", "text": text}

        elif etype.endswith("_end"):
            out = _content(ev.get("data", {}).get("output"))
            yield {"type": "node_end", "node": nid, "delta": {nid: out}}
            if nid == order[-1]:
                final_output = out
                yield {"type": "edge_taken", "source": nid, "target": "__end__",
                       "conditional": False, "condition_label": None}
                yield {"type": "state", "state": {"output": out}}

    yield {"type": "done", "state": {"output": final_output}}


async def _run_lcel_parallel(spec, input_data: dict) -> AsyncIterator[dict]:
    """RunnableParallel: 브랜치(map:key:*)를 블랙박스 노드로 동시 점등."""
    runnable = spec.build()
    yield {"type": "run_start", "graph_id": spec.id}

    started: set[str] = set()
    result: dict[str, Any] = {}

    async for ev in runnable.astream_events(input_data, version="v2"):
        tags = ev.get("tags") or []
        branch = None
        for t in tags:
            if t.startswith("map:key:"):
                branch = t.split("map:key:", 1)[1]
                break
        name = ev.get("name")
        etype = ev["event"]

        # 브랜치 래퍼(RunnableSequence)의 start/end 로 노드 점등/완료
        if branch is not None and name == "RunnableSequence":
            if etype == "on_chain_start" and branch not in started:
                started.add(branch)
                yield {"type": "edge_taken", "source": "__start__", "target": branch,
                       "conditional": False, "condition_label": None}
                yield {"type": "node_start", "node": branch}
            elif etype == "on_chain_end":
                out = _content(ev.get("data", {}).get("output"))
                result[branch] = out
                yield {"type": "node_end", "node": branch, "delta": {branch: out}}
                yield {"type": "edge_taken", "source": branch, "target": "__end__",
                       "conditional": False, "condition_label": None}
                yield {"type": "state", "state": _jsonify(result)}

    yield {"type": "done", "state": _jsonify(result)}


# =========================================================
# 공개 API
# =========================================================
def run_events(spec, input_data: dict) -> AsyncIterator[dict]:
    if spec.kind == "langgraph":
        return _run_langgraph(spec, input_data)
    if spec.lcel_shape == "parallel":
        return _run_lcel_parallel(spec, input_data)
    order = ["llm"] if spec.lcel_shape == "single" else ["prompt", "llm", "parser"]
    return _run_lcel_linear(spec, input_data, order)
