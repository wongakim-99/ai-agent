import { useEffect, useRef } from "react";

import type { RunState } from "../hooks/useGraphRun";
import type { RunEvent } from "../types";

function line(ev: RunEvent): string {
  switch (ev.type) {
    case "run_start":
      return `▷ 실행 시작 (${ev.graph_id})`;
    case "node_start":
      return `● ${ev.node} 시작`;
    case "node_end":
      return `✓ ${ev.node} 완료  ${Object.keys(ev.delta).join(", ")}`;
    case "edge_taken":
      return `→ ${ev.source} ▸ ${ev.target}${ev.conditional ? "  (분기)" : ""}`;
    case "token":
      return `· ${ev.node} 토큰`;
    case "state":
      return `⋯ State 갱신`;
    case "done":
      return `■ 완료`;
    case "error":
      return `⚠ 에러: ${ev.message}`;
  }
}

// 토큰 이벤트는 너무 많아 접어서 요약만.
export function EventTimeline({ runState }: { runState: RunState }) {
  const ref = useRef<HTMLDivElement>(null);
  const events = runState.log.filter((e) => e.type !== "token");

  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight });
  }, [runState.log.length]);

  return (
    <div className="panel">
      <div className="panel__title">실행 이벤트</div>
      <div className="timeline" ref={ref}>
        {events.length === 0 && <div className="panel__empty">아직 이벤트가 없습니다.</div>}
        {events.map((ev, i) => (
          <div key={i} className={`timeline__line timeline__line--${ev.type}`}>
            {line(ev)}
          </div>
        ))}
      </div>
    </div>
  );
}
