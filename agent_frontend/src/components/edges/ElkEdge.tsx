import { BaseEdge, EdgeLabelRenderer, getSmoothStepPath, type EdgeProps } from "@xyflow/react";

import type { FlowEdgeData, Point } from "../../layout/elkLayout";

// ELK 가 준 굴곡점들을 라운드 코너 직교 path 로 변환한다.
// 각 중간 점(코너)에서 앞뒤 세그먼트를 반지름 r 만큼 잘라 quadratic 으로 부드럽게 잇는다.
function pointsToRoundedPath(points: Point[], r = 8): string {
  if (points.length < 2) return "";
  if (points.length === 2) {
    return `M ${points[0].x},${points[0].y} L ${points[1].x},${points[1].y}`;
  }

  let d = `M ${points[0].x},${points[0].y}`;
  for (let i = 1; i < points.length - 1; i++) {
    const prev = points[i - 1];
    const cur = points[i];
    const next = points[i + 1];

    const inLen = Math.hypot(cur.x - prev.x, cur.y - prev.y);
    const outLen = Math.hypot(next.x - cur.x, next.y - cur.y);
    const rr = Math.min(r, inLen / 2, outLen / 2);

    // 코너 진입점(이전 방향으로 rr 앞), 진출점(다음 방향으로 rr 뒤)
    const enter = {
      x: cur.x - ((cur.x - prev.x) / (inLen || 1)) * rr,
      y: cur.y - ((cur.y - prev.y) / (inLen || 1)) * rr,
    };
    const exit = {
      x: cur.x + ((next.x - cur.x) / (outLen || 1)) * rr,
      y: cur.y + ((next.y - cur.y) / (outLen || 1)) * rr,
    };
    d += ` L ${enter.x},${enter.y} Q ${cur.x},${cur.y} ${exit.x},${exit.y}`;
  }
  const last = points[points.length - 1];
  d += ` L ${last.x},${last.y}`;
  return d;
}

export function ElkEdge(props: EdgeProps) {
  const { sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, markerEnd } = props;
  const data = props.data as FlowEdgeData | undefined;

  const path =
    data?.points && data.points.length >= 2
      ? pointsToRoundedPath(data.points)
      : getSmoothStepPath({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition })[0];

  const label = data?.conditionLabel;
  const pos = data?.labelPos;

  return (
    <>
      <BaseEdge id={props.id} path={path} markerEnd={markerEnd} />
      {label && pos && (
        <EdgeLabelRenderer>
          <div
            className="elk-edge__label"
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${pos.x}px, ${pos.y}px)`,
              pointerEvents: "none",
            }}
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}
