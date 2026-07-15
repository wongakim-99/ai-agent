import type { DateStep } from "../types";

interface Props {
  steps: DateStep[];
  /** 실행 중이면 마지막 줄에 "생각 중" 점을 붙인다 (완료된 메시지에서는 끈다). */
  running?: boolean;
}

const ICON: Record<DateStep["kind"], string> = {
  planner: "🧭",
  search: "🔍",
  curator: "✨",
};

/**
 * 에이전트가 노드를 하나씩 지날 때마다 쌓이는 진행/근거 목록.
 * 실행 중에는 실시간으로 늘어나고, 끝난 뒤에는 그 메시지의 기록으로 남는다.
 */
export function AgentSteps({ steps, running = false }: Props) {
  if (steps.length === 0 && !running) return null;

  return (
    <div className="steps">
      {steps.map((s, i) => (
        <div key={`${s.node}-${i}`} className={`steps__item steps__item--${s.kind}`}>
          <span className="steps__icon">{ICON[s.kind]}</span>
          <div className="steps__body">
            <div className="steps__title">
              {s.title}
              <span className="steps__node">{s.node}</span>
            </div>
            <ul className="steps__lines">
              {s.lines.map((line, j) => (
                <li key={j}>{line}</li>
              ))}
            </ul>
          </div>
        </div>
      ))}
      {running && (
        <div className="steps__item steps__item--pending">
          <span className="steps__icon">⏳</span>
          <div className="steps__body">
            <div className="steps__title steps__title--pending">
              {steps.length === 0 ? "요청을 읽는 중" : "다음 단계 진행 중"}
              <span className="steps__dots" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
