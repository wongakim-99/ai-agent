"""
그래프 → 프론트가 먹는 안정 nodes/edges JSON 으로 정규화한다.

- LangGraph: 컴파일 그래프의 .get_graph() 는 노드 id가 사람이 읽는 안정 문자열이라
  거의 그대로 쓴다.
- LCEL: .get_graph() 노드 id가 매 빌드마다 UUID라 불안정하다. 그래서 spec.lcel_shape
  ('single'/'linear'/'parallel')을 보고 역할 기반 안정 id(prompt/llm/parser,
  브랜치명)로 토폴로지를 직접 만든다. 이 안정 id는 streaming.py 의 실행 이벤트 매핑과
  정확히 일치한다.
"""
from __future__ import annotations

from typing import Any


def _node(nid: str, label: str, ntype: str, cond_target: bool = False) -> dict:
    return {"id": nid, "label": label, "type": ntype, "is_conditional_target": cond_target}


def _edge(src: str, tgt: str, conditional: bool = False, label: str | None = None) -> dict:
    return {"source": src, "target": tgt, "conditional": conditional, "condition_label": label}


# ---------------------------------------------------------
# LangGraph
# ---------------------------------------------------------
def _from_langgraph(spec) -> tuple[list[dict], list[dict]]:
    g = spec.build().get_graph()

    conditional_targets = {e.target for e in g.edges if e.conditional}

    nodes = []
    for nid, n in g.nodes.items():
        if nid == "__start__":
            nodes.append(_node(nid, "START", "start"))
        elif nid == "__end__":
            nodes.append(_node(nid, "END", "end"))
        else:
            # spec.node_types 에 역할이 지정돼 있으면 그 타입(router/agent/…)으로,
            # 없으면 기본 "node" 로 방출한다(완전 opt-in, 기존 챕터 무영향).
            ntype = spec.node_types.get(nid, "node")
            nodes.append(_node(nid, n.name, ntype, nid in conditional_targets))

    edges = []
    for e in g.edges:
        # 조건분기 엣지 라벨: edge.data 있으면 사용, 없으면 타깃 id 로 폴백.
        label = e.data if e.data else (e.target if e.conditional else None)
        edges.append(_edge(e.source, e.target, e.conditional, label))

    return nodes, edges


# ---------------------------------------------------------
# LCEL (모양 기반 안정 토폴로지)
# ---------------------------------------------------------
def _from_lcel(spec) -> tuple[list[dict], list[dict]]:
    shape = spec.lcel_shape

    if shape == "single":
        nodes = [
            _node("__start__", "START", "start"),
            _node("llm", "ChatOpenAI", "llm"),
            _node("__end__", "END", "end"),
        ]
        edges = [_edge("__start__", "llm"), _edge("llm", "__end__")]
        return nodes, edges

    if shape == "linear":
        parser_label = "JsonOutputParser" if spec.parser_kind == "json" else "StrOutputParser"
        nodes = [
            _node("__start__", "START", "start"),
            _node("prompt", "PromptTemplate", "prompt"),
            _node("llm", "ChatOpenAI", "llm"),
            _node("parser", parser_label, "parser"),
            _node("__end__", "END", "end"),
        ]
        edges = [
            _edge("__start__", "prompt"),
            _edge("prompt", "llm"),
            _edge("llm", "parser"),
            _edge("parser", "__end__"),
        ]
        return nodes, edges

    if shape == "parallel":
        nodes = [_node("__start__", "START", "start")]
        edges = []
        for br in spec.branches:
            nodes.append(_node(br, br, "branch"))
            edges.append(_edge("__start__", br))
            edges.append(_edge(br, "__end__"))
        nodes.append(_node("__end__", "END", "end"))
        return nodes, edges

    raise ValueError(f"알 수 없는 lcel_shape: {shape!r}")


# ---------------------------------------------------------
# 공개 API
# ---------------------------------------------------------
def build_topology(spec) -> dict[str, Any]:
    if spec.kind == "langgraph":
        nodes, edges = _from_langgraph(spec)
    else:
        nodes, edges = _from_lcel(spec)
    return {"id": spec.id, "kind": spec.kind, "nodes": nodes, "edges": edges}
