// 실행 상태기계: SSE 이벤트를 소비해 노드/엣지/State 상태로 환원한다.
import { useCallback, useReducer, useRef } from "react";

import { runGraph } from "../api/client";
import { edgeId, type NodeStatus, type RunEvent, type Topology } from "../types";

export interface RunState {
  running: boolean;
  nodeStatus: Record<string, NodeStatus>;
  takenEdges: Set<string>;
  dimmedEdges: Set<string>;
  dimmedNodes: Set<string>;
  state: Record<string, unknown>;
  tokens: Record<string, string>;
  log: RunEvent[];
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
  error: null,
};

type Action =
  | { kind: "reset" }
  | { kind: "event"; ev: RunEvent; topo: Topology | null }
  | { kind: "stopped" };

function reducer(s: RunState, action: Action): RunState {
  if (action.kind === "reset") {
    return { ...initial, running: true, takenEdges: new Set(), dimmedEdges: new Set(), dimmedNodes: new Set() };
  }
  if (action.kind === "stopped") {
    return { ...s, running: false };
  }

  const { ev, topo } = action;
  const log = [...s.log, ev];

  switch (ev.type) {
    case "run_start":
      return { ...initial, running: true, log };

    case "node_start":
      return { ...s, log, nodeStatus: { ...s.nodeStatus, [ev.node]: "running" } };

    case "token":
      return { ...s, log, tokens: { ...s.tokens, [ev.node]: (s.tokens[ev.node] ?? "") + ev.text } };

    case "node_end":
      return {
        ...s,
        log,
        nodeStatus: { ...s.nodeStatus, [ev.node]: "done" },
        state: { ...s.state, ...ev.delta },
      };

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
      return { ...s, log, takenEdges: taken, dimmedEdges, dimmedNodes };
    }

    case "state":
      return { ...s, log, state: ev.state };

    case "done":
      return {
        ...s,
        log,
        running: false,
        state: ev.state,
        // 남아있던 running 노드는 done 으로 마무리
        nodeStatus: Object.fromEntries(
          Object.entries(s.nodeStatus).map(([k, v]) => [k, v === "running" ? "done" : v]),
        ),
      };

    case "error":
      return { ...s, log, running: false, error: ev.message };

    default:
      return s;
  }
}

export function useGraphRun(topo: Topology | null) {
  const [state, dispatch] = useReducer(reducer, initial);
  const abortRef = useRef<AbortController | null>(null);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    dispatch({ kind: "stopped" });
  }, []);

  const run = useCallback(
    async (graphId: string, input: Record<string, unknown>) => {
      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      dispatch({ kind: "reset" });
      try {
        await runGraph(graphId, input, (ev) => dispatch({ kind: "event", ev, topo }), ctrl.signal);
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          dispatch({ kind: "event", ev: { type: "error", message: String(err) }, topo });
        }
      } finally {
        if (abortRef.current === ctrl) abortRef.current = null;
      }
    },
    [topo],
  );

  return { runState: state, run, stop };
}
