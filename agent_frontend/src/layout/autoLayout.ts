// 토폴로지 JSON → dagre 로 좌→우 레이어드 배치 → React Flow 노드/엣지.
// React Flow 는 좌표를 자동 배치하지 않으므로 dagre(동기)로 위치를 계산한다.
import dagre from "@dagrejs/dagre";
import { MarkerType, type Edge, type Node } from "@xyflow/react";

import { edgeId, type Topology } from "../types";

export const NODE_W = 172;
export const NODE_H = 54;

export interface GraphNodeData extends Record<string, unknown> {
  label: string;
  kind: string;
  status: "idle" | "running" | "done";
  dimmed: boolean;
  token?: string;
}

export interface FlowEdgeData extends Record<string, unknown> {
  conditional: boolean;
  conditionLabel: string | null;
}

export function layoutTopology(topo: Topology): {
  nodes: Node<GraphNodeData>[];
  edges: Edge<FlowEdgeData>[];
} {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "LR", nodesep: 34, ranksep: 96, marginx: 16, marginy: 16 });

  topo.nodes.forEach((n) => g.setNode(n.id, { width: NODE_W, height: NODE_H }));
  topo.edges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);

  const nodes: Node<GraphNodeData>[] = topo.nodes.map((n) => {
    const pos = g.node(n.id);
    return {
      id: n.id,
      type: "graphNode",
      position: { x: pos.x - NODE_W / 2, y: pos.y - NODE_H / 2 },
      data: { label: n.label, kind: n.type, status: "idle", dimmed: false },
    };
  });

  const edges: Edge<FlowEdgeData>[] = topo.edges.map((e) => ({
    id: edgeId(e.source, e.target),
    source: e.source,
    target: e.target,
    type: "smoothstep",
    markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
    data: { conditional: e.conditional, conditionLabel: e.condition_label },
    label: e.conditional ? e.condition_label ?? undefined : undefined,
  }));

  return { nodes, edges };
}
