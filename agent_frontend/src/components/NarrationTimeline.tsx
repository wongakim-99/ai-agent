import { useEffect, useRef, useState } from "react";

import type { RunState } from "../hooks/useGraphRun";
import type { RunEvent } from "../types";

const ICON: Record<string, string> = {
  node: "●",
  edge: "→",
  branch: "⑃",
  done: "■",
  error: "⚠",
  info: "▷",
};

// 원시 이벤트 → 한 줄(디버그용 "원시 로그" 토글에서 사용)
function rawLine(ev: RunEvent): string {
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

// 사람이 읽는 실행 해설(기본) + 원시 로그 토글.
export function NarrationTimeline({ runState }: { runState: RunState }) {
  const [raw, setRaw] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const rawEvents = runState.log.filter((e) => e.type !== "token");
  const count = raw ? rawEvents.length : runState.narration.length;

  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight });
  }, [count]);

  return (
    <div className="panel">
      <div className="panel__title panel__title--row">
        <span>실행 해설</span>
        <label className="panel__toggle">
          <input type="checkbox" checked={raw} onChange={(e) => setRaw(e.target.checked)} />
          원시 로그
        </label>
      </div>

      <div className="timeline" ref={ref}>
        {count === 0 && <div className="panel__empty">실행하면 여기에 해설이 표시됩니다.</div>}

        {!raw &&
          runState.narration.map((n) => (
            <div key={n.id} className={`narr narr--${n.icon}`}>
              <span className="narr__icon">{ICON[n.icon]}</span>
              <span className="narr__text">
                {n.text}
                {n.parallel && <span className="narr__parallel">⑃ 병렬</span>}
              </span>
            </div>
          ))}

        {raw &&
          rawEvents.map((ev, i) => (
            <div key={i} className={`timeline__line timeline__line--${ev.type}`}>
              {rawLine(ev)}
            </div>
          ))}
      </div>
    </div>
  );
}
