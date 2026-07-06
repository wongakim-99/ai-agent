import { useMemo } from "react";
import { Background, Controls, ReactFlow, type Edge, type Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { GraphNode } from "./nodes/GraphNode";
import { layoutTopology, type FlowEdgeData, type GraphNodeData } from "../layout/autoLayout";
import type { RunState } from "../hooks/useGraphRun";
import type { Topology } from "../types";

const nodeTypes = { graphNode: GraphNode };

interface Props {
  topology: Topology;
  runState: RunState;
}

// 토폴로지는 바뀔 때만 dagre 재배치(useMemo). 실행 상태는 매 렌더에서 스타일로만 덧입힌다.
export function GraphCanvas({ topology, runState }: Props) {
  const base = useMemo(() => layoutTopology(topology), [topology]);

  const nodes: Node<GraphNodeData>[] = base.nodes.map((n) => ({
    ...n,
    data: {
      ...n.data,
      status: runState.nodeStatus[n.id] ?? "idle",
      dimmed: runState.dimmedNodes.has(n.id),
      token: runState.tokens[n.id],
    },
  }));

  const edges: Edge<FlowEdgeData>[] = base.edges.map((e) => {
    const taken = runState.takenEdges.has(e.id);
    const dimmed = runState.dimmedEdges.has(e.id);
    return {
      ...e,
      animated: taken,
      className: taken ? "edge--taken" : dimmed ? "edge--dimmed" : "edge--idle",
    };
  });

  return (
    <div className="canvas">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
      >
        <Background gap={18} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
