// 실행 상태기계: (페이싱된) SSE 이벤트를 소비해 노드/엣지/State/해설 상태로 환원한다.
import { useCallback, useReducer, useRef, useState } from "react";

import { runGraph } from "../api/client";
import { createPacer, type Pacer } from "../lib/pacer";
import {
  edgeId,
  type NarrationLine,
  type NodeStatus,
  type RunEvent,
  type Topology,
} from "../types";

export interface RunState {
  running: boolean;
  nodeStatus: Record<string, NodeStatus>;
  takenEdges: Set<string>;
  dimmedEdges: Set<string>;
  dimmedNodes: Set<string>;
  state: Record<string, unknown>;
  tokens: Record<string, string>;
  log: RunEvent[];
  narration: NarrationLine[];
  changedKeys: Set<string>; // 가장 최근 node_end 가 바꾼 State 키(하이라이트용)
  error: string | null;
}

const initial: RunState = {
  running: false,
  nodeStatus: {},
  takenEdges: new Set(),
  dimmedEdges: new Set(),
  dimmedNodes: new Set(),
  state: {},
  tokens: {},
  log: [],
  narration: [],
  changedKeys: new Set(),
  error: null,
};

type Action =
  | { kind: "reset" }
  | { kind: "clear" }
  | { kind: "event"; ev: RunEvent; topo: Topology | null }
  | { kind: "stopped" };

// --- 나레이션 헬퍼 (topo 의 정적 doc + 실시간 State 로 사람 읽는 문장을 만든다) ---
function nodeLabel(topo: Topology | null, id: string): string {
  return topo?.nodes.find((n) => n.id === id)?.label ?? id;
}
function nodeDoc(topo: Topology | null, id: string): string | null {
  return topo?.nodes.find((n) => n.id === id)?.doc ?? null;
}
function edgeDoc(topo: Topology | null, source: string, target: string): string | null {
  return topo?.edges.find((e) => e.source === source && e.target === target)?.doc ?? null;
}
// "{state.키}" 를 분기 시점의 실제 State 값으로 치환 → "왜 이 길로 갔는지"
function fillState(doc: string, state: Record<string, unknown>): string {
  return doc.replace(/\{state\.(\w+)\}/g, (_, k: string) => {
    const v = state[k];
    if (v === undefined) return "?";
    return typeof v === "string" ? v : JSON.stringify(v);
  });
}
function pushLine(narration: NarrationLine[], line: Omit<NarrationLine, "id">): NarrationLine[] {
  return [...narration, { id: narration.length, ...line }];
}

function reducer(s: RunState, action: Action): RunState {
  if (action.kind === "reset") {
    return {
      ...initial,
      running: true,
      takenEdges: new Set(),
      dimmedEdges: new Set(),
      dimmedNodes: new Set(),
      changedKeys: new Set(),
    };
  }
  if (action.kind === "clear") {
    // 그래프 전환 시: 이전 실행의 State/해설/점등을 전부 비운다.
    return { ...initial, takenEdges: new Set(), dimmedEdges: new Set(), dimmedNodes: new Set(), changedKeys: new Set() };
  }
  if (action.kind === "stopped") {
    return { ...s, running: false };
  }

  const { ev, topo } = action;
  const log = [...s.log, ev];

  switch (ev.type) {
    case "run_start":
      return {
        ...initial,
        running: true,
        log,
        narration: pushLine([], { icon: "info", text: `▷ 실행 시작 (${ev.graph_id})` }),
      };

    case "node_start": {
      const label = nodeLabel(topo, ev.node);
      const doc = nodeDoc(topo, ev.node);
      // 이미 다른 노드가 running 이면 병렬 실행
      const parallel = Object.entries(s.nodeStatus).some(
        ([k, v]) => v === "running" && k !== ev.node,
      );
      const text = doc ? `${label} — ${doc}` : `'${label}' 노드 실행 시작`;
      return {
        ...s,
        log,
        nodeStatus: { ...s.nodeStatus, [ev.node]: "running" },
        narration: pushLine(s.narration, { icon: "node", text, parallel }),
      };
    }

    case "token":
      return { ...s, log, tokens: { ...s.tokens, [ev.node]: (s.tokens[ev.node] ?? "") + ev.text } };

    case "node_end": {
      const keys = Object.keys(ev.delta);
      const label = nodeLabel(topo, ev.node);
      const text = keys.length
        ? `✓ ${label} 완료 — State에 ${keys.join(", ")} 기록`
        : `✓ ${label} 완료`;
      return {
        ...s,
        log,
        nodeStatus: { ...s.nodeStatus, [ev.node]: "done" },
        state: { ...s.state, ...ev.delta },
        changedKeys: new Set(keys),
        narration: pushLine(s.narration, { icon: "node", text }),
      };
    }

    case "edge_taken": {
      const taken = new Set(s.takenEdges);
      taken.add(edgeId(ev.source, ev.target));
      const dimmedEdges = new Set(s.dimmedEdges);
      const dimmedNodes = new Set(s.dimmedNodes);
      // 조건분기: 같은 source 의 다른 conditional 형제 엣지/노드를 흐리게.
      if (ev.conditional && topo) {
        for (const e of topo.edges) {
          if (e.source === ev.source && e.conditional && e.target !== ev.target) {
            dimmedEdges.add(edgeId(e.source, e.target));
            dimmedNodes.add(e.target);
          }
        }
      }
      // 해설: 조건 엣지이거나 doc 이 있을 때만(비조건 무doc 엣지는 노이즈라 생략)
      let narration = s.narration;
      const doc = edgeDoc(topo, ev.source, ev.target);
      if (doc) {
        narration = pushLine(narration, { icon: "branch", text: fillState(doc, s.state) });
      } else if (ev.conditional && ev.target !== "__end__") {
        const src = nodeLabel(topo, ev.source);
        const tgt = nodeLabel(topo, ev.target);
        narration = pushLine(narration, { icon: "branch", text: `조건 분기: ${src} → ${tgt}` });
      }
      return { ...s, log, takenEdges: taken, dimmedEdges, dimmedNodes, narration };
    }

    case "state":
      return { ...s, log, state: ev.state };

    case "done":
      return {
        ...s,
        log,
        running: false,
        state: ev.state,
        changedKeys: new Set(),
        nodeStatus: Object.fromEntries(
          Object.entries(s.nodeStatus).map(([k, v]) => [k, v === "running" ? "done" : v]),
        ),
        narration: pushLine(s.narration, { icon: "done", text: "■ 실행 완료" }),
      };

    case "error":
      return {
        ...s,
        log,
        running: false,
        error: ev.message,
        narration: pushLine(s.narration, { icon: "error", text: `⚠ 에러: ${ev.message}` }),
      };

    default:
      return s;
  }
}

export function useGraphRun(topo: Topology | null) {
  const [state, dispatch] = useReducer(reducer, initial);
  const abortRef = useRef<AbortController | null>(null);
  const [speed, setSpeedState] = useState(1);

  // topo 는 ref 로 참조해 pacer 콜백을 재생성하지 않는다.
  const topoRef = useRef(topo);
  topoRef.current = topo;

  // pacer 는 한 번만 생성(수신 이벤트를 페이싱해 reducer 로 흘린다).
  const pacerRef = useRef<Pacer>();
  if (!pacerRef.current) {
    pacerRef.current = createPacer((ev) => dispatch({ kind: "event", ev, topo: topoRef.current }));
  }

  const setSpeed = useCallback((mult: number) => {
    setSpeedState(mult);
    pacerRef.current!.setSpeed(mult);
  }, []);

  const skip = useCallback(() => pacerRef.current!.flush(), []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    pacerRef.current!.clear();
    dispatch({ kind: "stopped" });
  }, []);

  // 그래프 전환용: 실행 중단 + 이전 실행 결과(State/해설/점등) 완전 초기화.
  const clear = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    pacerRef.current!.clear();
    dispatch({ kind: "clear" });
  }, []);

  const run = useCallback(async (graphId: string, input: Record<string, unknown>) => {
    abortRef.current?.abort();
    pacerRef.current!.clear();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    dispatch({ kind: "reset" });
    try {
      await runGraph(graphId, input, (ev) => pacerRef.current!.push(ev), ctrl.signal);
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        pacerRef.current!.push({ type: "error", message: String(err) });
      }
    } finally {
      if (abortRef.current === ctrl) abortRef.current = null;
    }
  }, []);

  return { runState: state, run, stop, clear, speed, setSpeed, skip };
}
