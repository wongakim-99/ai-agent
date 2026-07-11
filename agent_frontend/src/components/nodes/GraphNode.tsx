import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";

import type { GraphNodeData } from "../../layout/elkLayout";

type GraphNodeType = Node<GraphNodeData, "graphNode">;

// 커스텀 노드: 종류(start/end/llm/…)별 색 + 상태(idle/running/done)별 강조.
// 상태를 색만이 아니라 색+아이콘+테두리 3중으로 인코딩한다(색약 대응).
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
    <div className={cls} title={data.doc ?? undefined}>
      {!isStart && <Handle type="target" position={Position.Left} />}
      <div className="gnode__label">{data.label}</div>
      {data.status === "running" && <div className="gnode__spinner" aria-hidden />}
      {data.status === "done" && <div className="gnode__check" aria-hidden>✓</div>}
      {!isEnd && <Handle type="source" position={Position.Right} />}
    </div>
  );
}
