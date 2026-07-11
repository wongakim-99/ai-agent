import { useMemo, useState } from "react";
import { Panel } from "@xyflow/react";

import type { Topology } from "../types";

// 노드 역할 타입 → 범례 라벨 (현재 그래프에 존재하는 것만 동적으로 표시)
const ROLE_LABELS: Record<string, string> = {
  router: "라우터 (분기 결정)",
  agent: "에이전트 (조회 일꾼)",
  fallback: "fallback",
  reporter: "합류 리포터",
  prompt: "프롬프트",
  llm: "LLM",
  parser: "파서",
  branch: "병렬 브랜치",
  node: "노드",
};

export function Legend({ topology }: { topology: Topology }) {
  const [open, setOpen] = useState(true);

  // 이 그래프에 실제로 등장하는 역할만(start/end 제외) 추린다.
  const roles = useMemo(() => {
    const seen = new Set<string>();
    for (const n of topology.nodes) {
      if (n.type !== "start" && n.type !== "end") seen.add(n.type);
    }
    return [...seen];
  }, [topology]);

  return (
    <Panel position="bottom-left" className="legend">
      <button className="legend__toggle" onClick={() => setOpen((v) => !v)}>
        범례 {open ? "▾" : "▸"}
      </button>
      {open && (
        <div className="legend__body">
          <div className="legend__group">
            {roles.map((r) => (
              <div key={r} className="legend__row">
                <span className={`legend__swatch gnode--${r}`} />
                <span>{ROLE_LABELS[r] ?? r}</span>
              </div>
            ))}
          </div>
          <div className="legend__group">
            <div className="legend__row">
              <span className="legend__line legend__line--taken" />
              <span>실행된 경로</span>
            </div>
            <div className="legend__row">
              <span className="legend__line legend__line--dim" />
              <span>선택 안 된 분기</span>
            </div>
            <div className="legend__row">
              <span className="legend__line legend__line--idle" />
              <span>대기</span>
            </div>
          </div>
          <div className="legend__group">
            <div className="legend__row">
              <span className="legend__dot legend__dot--running" />
              <span>실행 중</span>
            </div>
            <div className="legend__row">
              <span className="legend__dot legend__dot--done" />
              <span>완료</span>
            </div>
          </div>
        </div>
      )}
    </Panel>
  );
}
