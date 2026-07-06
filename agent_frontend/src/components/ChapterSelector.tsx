import type { GraphSummary } from "../types";

interface Props {
  graphs: GraphSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

// 챕터별로 묶은 패턴 선택기.
export function ChapterSelector({ graphs, selectedId, onSelect }: Props) {
  const chapters = [...new Set(graphs.map((g) => g.chapter))].sort();

  return (
    <div className="selector">
      {chapters.map((ch) => (
        <div key={ch} className="selector__group">
          <span className="selector__chapter">챕터 {ch}</span>
          <div className="selector__chips">
            {graphs
              .filter((g) => g.chapter === ch)
              .map((g) => (
                <button
                  key={g.id}
                  className={`chip ${g.id === selectedId ? "chip--active" : ""} chip--${g.kind}`}
                  onClick={() => onSelect(g.id)}
                  title={g.title}
                >
                  {g.id}
                </button>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
