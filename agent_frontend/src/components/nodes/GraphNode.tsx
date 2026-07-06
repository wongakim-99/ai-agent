import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";

import type { GraphNodeData } from "../../layout/autoLayout";

type GraphNodeType = Node<GraphNodeData, "graphNode">;

// 커스텀 노드: 종류(start/end/llm/…)별 색 + 상태(idle/running/done)별 강조.
export function GraphNode({ data }: NodeProps<GraphNodeType>) {
  const isStart = data.kind === "start";
  const isEnd = data.kind === "end";
  const cls = [
    "gnode",
    `gnode--${data.kind}`,
    `gnode--${data.status}`,
    data.dimmed ? "gnode--dimmed" : "",
  ].join(" ");

  return (
    <div className={cls}>
      {!isStart && <Handle type="target" position={Position.Left} />}
      <div className="gnode__label">{data.label}</div>
      {data.status === "running" && <div className="gnode__spinner" aria-hidden />}
      {!isEnd && <Handle type="source" position={Position.Right} />}
    </div>
  );
}
