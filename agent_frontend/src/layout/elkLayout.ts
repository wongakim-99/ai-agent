// 토폴로지 JSON → ELK(layered, 직교 라우팅)로 배치 → React Flow 노드/엣지.
// dagre 는 노드만 배치하고 엣지 경로를 계산하지 않아 레이어를 건너뛰는 엣지가
// 노드를 관통했다. ELK 는 엣지의 실제 경로(sections: 시작/굴곡점/끝)까지 계산해주므로
// 노드가 많아지거나(챕터5) 사이클이 생겨도 선이 꼬이지 않는다.
// 계산된 경로는 커스텀 엣지(ElkEdge)가 그대로 그린다.
import ELK from "elkjs/lib/elk.bundled.js";
import type { Edge, Node } from "@xyflow/react";

import { edgeId, type Topology } from "../types";

export const NODE_W = 172;
export const NODE_H = 54;

const elk = new ELK();

export interface GraphNodeData extends Record<string, unknown> {
  label: string;
  kind: string;
  status: "idle" | "running" | "done";
  dimmed: boolean;
  token?: string;
  doc?: string | null;
}

export interface Point {
  x: number;
  y: number;
}

export interface FlowEdgeData extends Record<string, unknown> {
  conditional: boolean;
  conditionLabel: string | null;
  doc: string | null;
  points?: Point[]; // ELK 가 계산한 실제 경로(시작→굴곡점들→끝)
  labelPos?: Point; // ELK 가 계산한 라벨 좌표
}

export interface LayoutResult {
  id: string; // 어느 그래프의 레이아웃인지(전환 중 stale 판별용)
  nodes: Node<GraphNodeData>[];
  edges: Edge<FlowEdgeData>[];
  width: number;
  height: number;
}

// layered 알고리즘 옵션. 직교 라우팅 + 넉넉한 간격으로 관통/겹침을 막는다.
const layoutOptions: Record<string, string> = {
  "elk.algorithm": "layered",
  "elk.direction": "RIGHT",
  "elk.edgeRouting": "ORTHOGONAL",
  "elk.layered.spacing.nodeNodeBetweenLayers": "90",
  "elk.spacing.nodeNode": "48",
  "elk.spacing.edgeNode": "24",
  "elk.spacing.edgeEdge": "14",
  "elk.layered.nodePlacement.strategy": "BRANDES_KOEPF",
  "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
  "elk.layered.cycleBreaking.strategy": "GREEDY", // 챕터5 루프(사이클) 대비
  "elk.layered.mergeEdges": "false",
  "elk.edgeLabels.placement": "CENTER",
};

// 라벨 폭 대략 추정(ELK 가 겹치지 않게 배치할 공간 확보용).
function labelBox(text: string) {
  return { width: text.length * 12 + 16, height: 20 };
}

export async function layoutTopology(topo: Topology): Promise<LayoutResult> {
  const graph = {
    id: "root",
    layoutOptions,
    children: topo.nodes.map((n) => ({ id: n.id, width: NODE_W, height: NODE_H })),
    edges: topo.edges.map((e) => {
      const label = e.conditional ? e.condition_label : null;
      return {
        id: edgeId(e.source, e.target),
        sources: [e.source],
        targets: [e.target],
        ...(label ? { labels: [{ text: label, ...labelBox(label) }] } : {}),
      };
    }),
  };

  interface ElkLaidNode {
    id: string;
    x?: number;
    y?: number;
  }
  interface ElkLaidEdge {
    id: string;
    sections?: { startPoint: Point; endPoint: Point; bendPoints?: Point[] }[];
    labels?: { x: number; y: number }[];
  }
  interface ElkLaidGraph {
    children?: ElkLaidNode[];
    edges?: ElkLaidEdge[];
    width?: number;
    height?: number;
  }

  const laid = (await elk.layout(graph)) as unknown as ElkLaidGraph;

  const posOf = new Map<string, Point>();
  for (const c of laid.children ?? []) {
    posOf.set(c.id, { x: c.x ?? 0, y: c.y ?? 0 });
  }

  const nodes: Node<GraphNodeData>[] = topo.nodes.map((n) => {
    const p = posOf.get(n.id) ?? { x: 0, y: 0 };
    return {
      id: n.id,
      type: "graphNode",
      position: { x: p.x, y: p.y },
      data: { label: n.label, kind: n.type, status: "idle", dimmed: false, doc: n.doc },
    };
  });

  const laidEdges = new Map((laid.edges ?? []).map((e) => [e.id, e]));

  const edges: Edge<FlowEdgeData>[] = topo.edges.map((e) => {
    const id = edgeId(e.source, e.target);
    const le = laidEdges.get(id);
    const sec = le?.sections?.[0];
    const points = sec
      ? [sec.startPoint, ...(sec.bendPoints ?? []), sec.endPoint]
      : undefined;
    const lbl = le?.labels?.[0];
    return {
      id,
      source: e.source,
      target: e.target,
      type: "elk",
      data: {
        conditional: e.conditional,
        conditionLabel: e.conditional ? e.condition_label : null,
        doc: e.doc ?? null,
        points,
        labelPos: lbl ? { x: lbl.x, y: lbl.y } : undefined,
      },
    };
  });

  return { id: topo.id, nodes, edges, width: laid.width ?? 0, height: laid.height ?? 0 };
}
