import { useMemo } from "react";

import type { GraphSummary } from "../types";

interface Props {
  graphs: GraphSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

// 챕터 번호 → 그룹 제목
const CHAPTER_TITLES: Record<number, string> = {
  2: "챕터 2 — LCEL 체인",
  3: "챕터 3 — LangGraph 기본",
  4: "챕터 4 — Multi-Agent",
};

// id 프리픽스("3-1 ")를 제목에서 떼어 중복 표기를 줄인다.
function stripId(id: string, title: string): string {
  return title.startsWith(id) ? title.slice(id.length).replace(/^[\s.—-]+/, "") : title;
}

// 좌측 사이드바: 챕터별 그룹 + 그래프 항목. 선택 항목 아래 개념 설명을 인라인 확장.
export function GraphSidebar({ graphs, selectedId, onSelect }: Props) {
  const chapters = useMemo(
    () => [...new Set(graphs.map((g) => g.chapter))].sort((a, b) => a - b),
    [graphs],
  );

  return (
    <nav className="sidebar">
      {chapters.map((ch) => (
        <div key={ch} className="sidebar__group">
          <div className="sidebar__group-title">{CHAPTER_TITLES[ch] ?? `챕터 ${ch}`}</div>
          {graphs
            .filter((g) => g.chapter === ch)
            .map((g) => {
              const active = g.id === selectedId;
              return (
                <div key={g.id} className="sidebar__item-wrap">
                  <button
                    className={`sidebar__item ${active ? "sidebar__item--active" : ""}`}
                    onClick={() => onSelect(g.id)}
                  >
                    <span className="sidebar__id">{g.id}</span>
                    <span className="sidebar__name">{stripId(g.id, g.title)}</span>
                    <span className={`badge badge--${g.kind}`}>{g.kind}</span>
                  </button>
                  {active && g.concept && <p className="sidebar__concept">{g.concept}</p>}
                </div>
              );
            })}
        </div>
      ))}
    </nav>
  );
}
