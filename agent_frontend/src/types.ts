// 백엔드 스키마(schemas.py)와 대응하는 프론트 타입.

export interface GraphSummary {
  id: string;
  chapter: number;
  title: string;
  kind: "lcel" | "langgraph";
  concept: string;
  input_example: Record<string, unknown>;
}

export interface TopologyNode {
  id: string;
  label: string;
  type: string; // start | end | node | prompt | llm | parser | branch | router | agent | fallback | reporter
  is_conditional_target: boolean;
  doc?: string | null; // 교육용 노드 해설 (opt-in)
}

export interface TopologyEdge {
  source: string;
  target: string;
  conditional: boolean;
  condition_label: string | null;
  doc?: string | null; // 교육용 분기 해설 ("{state.키}" 치환 대상)
}

export interface Topology {
  id: string;
  kind: string;
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}

// SSE 실행 이벤트 (streaming.py 와 1:1)
export type RunEvent =
  | { type: "run_start"; graph_id: string }
  | { type: "node_start"; node: string }
  | { type: "token"; node: string; text: string }
  | { type: "node_end"; node: string; delta: Record<string, unknown> }
  | {
      type: "edge_taken";
      source: string;
      target: string;
      conditional: boolean;
      condition_label: string | null;
    }
  | { type: "state"; state: Record<string, unknown> }
  | { type: "done"; state: Record<string, unknown> }
  | { type: "error"; message: string; node?: string };

export type NodeStatus = "idle" | "running" | "done";

// 사람이 읽는 실행 해설 한 줄 (원시 이벤트를 교육용 문장으로 변환한 결과)
export interface NarrationLine {
  id: number;
  icon: "node" | "edge" | "branch" | "done" | "error" | "info";
  text: string;
  parallel?: boolean; // 다른 노드와 동시에 실행 중이면 true
}

export const edgeId = (source: string, target: string) => `${source}->${target}`;
