import { useEffect, useRef, useState } from "react";
import {
  Background,
  Controls,
  ReactFlow,
  ReactFlowProvider,
  useNodesInitialized,
  useReactFlow,
  type ColorMode,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { GraphNode } from "./nodes/GraphNode";
import { ElkEdge } from "./edges/ElkEdge";
import { Legend } from "./Legend";
import { layoutTopology, type FlowEdgeData, type GraphNodeData, type LayoutResult } from "../layout/elkLayout";
import type { RunState } from "../hooks/useGraphRun";
import type { Topology } from "../types";

const nodeTypes = { graphNode: GraphNode };
const edgeTypes = { elk: ElkEdge };

interface Props {
  topology: Topology;
  runState: RunState;
  colorMode?: ColorMode;
}

export function GraphCanvas(props: Props) {
  return (
    <ReactFlowProvider>
      <Flow {...props} />
    </ReactFlowProvider>
  );
}

function Flow({ topology, runState, colorMode = "dark" }: Props) {
  const [layout, setLayout] = useState<LayoutResult | null>(null);
  const { fitView } = useReactFlow();
  const nodesInitialized = useNodesInitialized();
  const fittedFor = useRef<string>("");

  // ELK 는 비동기라 useMemo 대신 effect. alive 플래그로 빠른 그래프 전환/StrictMode 이중 실행 가드.
  // (layout 을 null 로 비우지 않아 그래프 전환 시 ReactFlow 를 언마운트하지 않는다 → 측정 안정)
  useEffect(() => {
    let alive = true;
    layoutTopology(topology).then((r) => {
      if (alive) setLayout(r);
    });
    return () => {
      alive = false;
    };
  }, [topology]);

  // 새 그래프의 노드가 실제로 DOM 에 측정된 뒤(nodesInitialized=true)에만 fitView.
  // 새 노드를 넘기면 nodesInitialized 가 잠시 false 로 떨어졌다가 측정 후 true 가 되므로,
  // 측정 전 stale fit(잘림)을 피한다. fittedFor 로 그래프당 1회만 맞춘다.
  useEffect(() => {
    if (!layout || layout.id !== topology.id) return; // 아직 이전 그래프 레이아웃이면 대기
    if (!nodesInitialized) return;
    if (fittedFor.current === topology.id) return;
    fittedFor.current = topology.id;
    fitView({ padding: 0.2, duration: 200 });
  }, [layout, nodesInitialized, topology.id, fitView]);

  // 창 리사이즈 시 다시 화면에 맞춤(디바운스).
  useEffect(() => {
    let t: number | undefined;
    const onResize = () => {
      window.clearTimeout(t);
      t = window.setTimeout(() => fitView({ padding: 0.2 }), 150);
    };
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      window.clearTimeout(t);
    };
  }, [fitView]);

  // 아직 첫 레이아웃 전이면 로딩만.
  if (!layout) {
    return (
      <div className="canvas">
        <div className="app__loading">레이아웃 계산 중…</div>
      </div>
    );
  }

  const nodes: Node<GraphNodeData>[] = layout.nodes.map((n) => ({
    ...n,
    data: {
      ...n.data,
      status: runState.nodeStatus[n.id] ?? "idle",
      dimmed: runState.dimmedNodes.has(n.id),
      token: runState.tokens[n.id],
    },
  }));

  const edges: Edge<FlowEdgeData>[] = layout.edges.map((e) => {
    const taken = runState.takenEdges.has(e.id);
    const dimmed = runState.dimmedEdges.has(e.id);
    return {
      ...e,
      className: taken ? "edge--taken" : dimmed ? "edge--dimmed" : "edge--idle",
      markerEnd: taken ? "url(#arrow-taken)" : dimmed ? "url(#arrow-dim)" : "url(#arrow-idle)",
    };
  });

  return (
    <div className="canvas">
      {/* 상태별 화살촉(얇은 셰브런). React Flow 기본 삼각형 대신 사용. */}
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <defs>
          {(
            [
              ["arrow-idle", "var(--edge)", 1.8, 1],
              ["arrow-taken", "var(--accent)", 2.2, 1],
              ["arrow-dim", "var(--edge)", 1.6, 0.4],
            ] as const
          ).map(([id, stroke, w, op]) => (
            <marker
              key={id}
              id={id}
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="8"
              markerHeight="8"
              orient="auto-start-reverse"
            >
              <path
                d="M1,1 L9,5 L1,9"
                fill="none"
                stroke={stroke}
                strokeWidth={w}
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity={op}
              />
            </marker>
          ))}
        </defs>
      </svg>

      <ReactFlow
        colorMode={colorMode}
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={1.6}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
      >
        <Background gap={18} />
        <Controls showInteractive={false} />
        <Legend topology={topology} />
      </ReactFlow>
    </div>
  );
}
