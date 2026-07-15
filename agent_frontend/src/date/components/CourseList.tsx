import { CHAR_MS, useTypewriter } from "../hooks/useTypewriter";
import type { CourseStop } from "../types";

interface Props {
  region: string;
  summary: string;
  course: CourseStop[];
  /** 방금 도착한 답변이면 요약을 타이핑하고 코스를 하나씩 띄운다 (과거 메시지는 즉시) */
  animate?: boolean;
}

const CATEGORY_LABEL: Record<string, string> = {
  restaurant: "맛집",
  cafe: "카페",
  activity: "활동",
};

export function CourseList({ region, summary, course, animate = false }: Props) {
  // 훅은 조기 return 보다 위에 있어야 한다 (코스가 비어도 호출 순서가 바뀌지 않게)
  const { shown, typing } = useTypewriter(summary, animate);

  if (course.length === 0) {
    return (
      <div className="cl cl--empty">
        추천할 코스를 찾지 못했어요. 다른 지역이나 키워드로 다시 시도해보세요.
      </div>
    );
  }

  return (
    <div className="cl">
      <div className="cl__head">
        <div className="cl__region">📍 {region}</div>
        <p className={`cl__summary${typing ? " cl__summary--typing" : ""}`}>{shown}</p>
      </div>
      {/* 요약을 다 친 뒤 코스가 순서대로 뜬다 (지연은 CSS 로만 — 렌더는 한 번에) */}
      <ol className={`cl__list${animate ? " cl__list--stagger" : ""}`}>
        {course.map((s, i) => (
          <li
            key={s.step}
            className="cl__item"
            style={
              animate
                ? { animationDelay: `${summary.length * CHAR_MS + i * 110}ms` } // 요약을 다 친 직후부터
                : undefined
            }
          >
            <div className="cl__step">{s.step}</div>
            <div className="cl__body">
              <div className="cl__line1">
                <span className={`cl__tag cl__tag--${s.category}`}>
                  {CATEGORY_LABEL[s.category] ?? s.category}
                </span>
                <span className="cl__time">{s.time_slot}</span>
              </div>
              {s.url ? (
                <a className="cl__name" href={s.url} target="_blank" rel="noreferrer">
                  {s.place_name} ↗
                </a>
              ) : (
                <span className="cl__name">{s.place_name}</span>
              )}
              <div className="cl__addr">{s.address}</div>
              <div className="cl__reason">{s.reason}</div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
